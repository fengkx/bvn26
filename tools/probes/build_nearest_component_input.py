"""Preserve an original indexed nearest leaf and independently materialize its bytes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import uuid
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_minimal_swf import rect,tag
from tools.probes.inventory_bitmap_roundtrip import decode_lossless

HARNESS=Path('tools/probes/flash_filters/nearest-component-input.as')
GRAPH=Path('evidence/importer-loud-fail/r156/main-fixture.json.gz')


def source_matrix(payload):
    owner,frame_count=struct.unpack_from('<HH',payload)
    assert owner==298 and frame_count>0
    offset=4
    while offset<len(payload):
        header=struct.unpack_from('<H',payload,offset)[0];offset+=2;length=header&63
        if length==63:length=struct.unpack_from('<I',payload,offset)[0];offset+=4
        data=payload[offset:offset+length];offset+=length
        if header>>6==1:break
        if header>>6!=70:continue
        assert data[:6]==bytes.fromhex('0e0101002901')
        bits=''.join(f'{v:08b}' for v in data[6:]);position=0
        def read(width,signed=False):
            nonlocal position
            assert position+width<=len(bits)
            value=int(bits[position:position+width],2) if width else 0;position+=width
            return value-(1<<width) if signed and width and value&(1<<(width-1)) else value
        a=d=1
        if read(1):
            width=read(5);a=read(width,True)/65536;d=read(width,True)/65536
        b=c=0
        if read(1):
            width=read(5);b=read(width,True)/65536;c=read(width,True)/65536
        width=read(5);tx=read(width,True);ty=read(width,True)
        return [a,b,c,d,tx/20,ty/20],data[6:6+(position+7)//8].hex()
    raise ValueError('Missing source frame1 placement matrix')


def build(output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    graph=json.loads(gzip.decompress((ROOT/GRAPH).read_bytes()));leaf=graph['leaves']['282'];case=graph['case']
    source=ROOT/case['source']['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==case['source']['sha256']
    assert leaf['fill']=={'type':'FILLSTYLE','bitmapId':'281','fillStyleType':'67'} and leaf['smooth_sampling'] is False
    assert leaf['fill_masks']==[[[[137.0,0.0],[137.0,200.0],[0.0,200.0],[0.0,0.0]]]]
    raw={struct.unpack_from('<H',p)[0]:(p,r) for code,p,r in source_tags(source) if code in (2,36) and struct.unpack_from('<H',p)[0] in (281,282)}
    assert set(raw)=={281,282}
    for cid,(_,r) in raw.items():assert hashlib.sha256(r).hexdigest()==graph['raw_tag_sha256'][str(cid)]
    cid,w,h,pixels=decode_lossless(raw[281][0]);assert raw[281][0][2]==3 and [cid,w,h]==[281,137,200]
    assert pixels==leaf['pixels_premultiplied'] and all(p[3] in (0,255) for p in pixels)
    normal=case['normalization'];assert normal['scale']==1
    owner_payload,owner_raw=next((p,r) for code,p,r in source_tags(source) if code==39 and struct.unpack_from('<H',p)[0]==298)
    matrix,matrix_hex=source_matrix(owner_payload)
    cases=[[1,0,0,1,0,0,100,100],matrix+[normal['x'],normal['y']]]
    output.mkdir(parents=True,exist_ok=True);(output/'game').mkdir(exist_ok=True);(output/'scripts/frame_1').mkdir(parents=True,exist_ok=True)
    run='nearest-component-'+uuid.uuid4().hex[:12]
    script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('CASES',json.dumps(cases,separators=(',',':'))).replace('WIDTH',str(w)).replace('HEIGHT',str(h))
    (output/'scripts/frame_1/DoAction.as').write_text(script)
    wrapper=struct.pack('<HH',60000,1)+tag(26,b'\x06'+struct.pack('<HH',1,282)+b'\0')+tag(1)+tag(0)
    exports=struct.pack('<H',2)+struct.pack('<H',60000)+b'leaf\0'+struct.pack('<H',281)+b'sourceBitmap\0'
    body=rect(0,12000,0,8000)+struct.pack('<HH',30*256,1)+raw[281][1]+raw[282][1]+tag(39,wrapper)+tag(56,exports)+tag(12,b'\0')+tag(1)+tag(0)
    (output/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(output/'base.swf'),str(output/'game/main.swf'),str(output/'scripts')],check=True,stdout=subprocess.DEVNULL)
    after={struct.unpack_from('<H',p)[0]:r for code,p,r in source_tags(output/'game/main.swf') if code in (2,36) and struct.unpack_from('<H',p)[0] in raw}
    assert after=={cid:r for cid,(_,r) in raw.items()}
    fixture={'source_owner_sha256':hashlib.sha256(owner_raw).hexdigest(),'source_matrix_bytes':matrix_hex,'leaf':leaf,'cases':cases,'target_size':[600,400],'raw_tag_sha256':{str(cid):hashlib.sha256(r).hexdigest() for cid,(_,r) in raw.items()},'production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(fixture,separators=(',',':'))+'\n')
    metadata={'run_id':run,'source':case['source']['path'],'source_sha256':case['source']['sha256'],'graph_sha256':hashlib.sha256((ROOT/GRAPH).read_bytes()).hexdigest(),
              'raw_tags_preserved':True,'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),
              'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),
              'outputs_sha256':{'game/main.swf':hashlib.sha256((output/'game/main.swf').read_bytes()).hexdigest()},'production_admitted':False}
    (output/'build.json').write_text(json.dumps(metadata,indent=2)+'\n');return metadata


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();print(build(a.output,a.ffdec.resolve())['run_id'])
