"""Retain raw source shapes and alter only their parsed active bitmap sampling byte."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import uuid
import zlib
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_minimal_swf import rect,tag
from tools.probes.build_jinye_affine_controls import controls as old_controls

HARNESS=Path('tools/probes/flash_filters/jinye-sampling-modes.as')


def source_pixel(x,y):return [2*x,6*y,73,255]


def active_fill_offset(payload):
    pos=16
    def read(n):
        nonlocal pos
        assert pos+n<=len(payload)*8
        result=0
        for _ in range(n):result=(result<<1)|((payload[pos//8]>>(7-pos%8))&1);pos+=1
        return result
    width=read(5);read(4*width);pos=(pos+7)//8*8
    count=read(8);assert count==2
    styles=[]
    for _ in range(count):
        offset=pos//8;kind=read(8)
        assert kind==65
        low=read(8);high=read(8);bitmap=low+256*high
        if read(1):width=read(5);read(2*width)
        if read(1):width=read(5);read(2*width)
        width=read(5);read(2*width);pos=(pos+7)//8*8
        styles.append({'offset':offset,'type':kind,'bitmap':bitmap})
    assert [s['bitmap'] for s in styles]==[65535,55]
    return styles[1]['offset'],styles


def sampling_tag(payload,raw,mode):
    assert mode in (65,67)
    offset,styles=active_fill_offset(payload)
    header=6 if struct.unpack_from('<H',raw)[0]&63==63 else 2
    assert raw[header:]==payload
    result=bytearray(raw);result[header+offset]=mode
    differences=[i for i,(a,b) in enumerate(zip(raw,result)) if a!=b]
    assert differences==([] if mode==65 else [header+offset])
    return bytes(result),{'payload_offset':offset,'tag_offset':header+offset,'styles':styles,'changed_offsets':differences}


def controls():
    graph,old=old_controls();cases=[]
    for base in old:
        if base['source']!=0 or base['draw'][0]==2:continue
        vertical=next(c for c in old if c['shape']==base['shape'] and c['draw']==base['draw'] and c['source']==1)
        cases.append({**base,'id':len(cases),'base_h':base['id'],'base_v':vertical['id']})
    assert len(cases)==4
    return graph,cases,[None]+[[left,0,1,96] for left in (46,47,48)]


def build(output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    graph,cases,clips=controls();source=ROOT/graph['source']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==graph['source']['sha256']
    raw={struct.unpack_from('<H',p)[0]:(p,r) for code,p,r in source_tags(source) if code==2 and struct.unpack_from('<H',p)[0] in (56,57)}
    assert set(raw)=={56,57} and all(hashlib.sha256(r).hexdigest()==graph['raw_tag_sha256'][str(cid)] for cid,(_,r) in raw.items())
    output.mkdir(parents=True,exist_ok=True)
    fixture={'cases':cases,'clips':clips,'modes':[65,67],'source_graph':graph,'size':[96,96],'source_size':[92,40],'production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n');reports=[]
    rgba=[source_pixel(x,y) for y in range(40) for x in range(92)]
    payload=struct.pack('<HBHH',55,5,92,40)+zlib.compress(bytes(c for r,g,b,a in rgba for c in (a,r,g,b)))
    bitmap=struct.pack('<HI',(36<<6)|63,len(payload))+payload
    for mode in (65,67):
        folder=output/f'mode{mode}';(folder/'game').mkdir(parents=True,exist_ok=True);(folder/'scripts/frame_1').mkdir(parents=True,exist_ok=True)
        shapes={};changes={};wrappers=[];exports=struct.pack('<H',3)+struct.pack('<H',55)+b'sourceBitmap\0'
        for cid,(p,r) in raw.items():shapes[cid],changes[str(cid)]=sampling_tag(p,r,mode)
        for cid in (56,57):
            wid=60000+cid-56;wrappers.append(tag(39,struct.pack('<HH',wid,1)+tag(26,b'\x06'+struct.pack('<HH',1,cid)+b'\0')+tag(1)+tag(0)))
            exports+=struct.pack('<H',wid)+f'leaf{cid}'.encode()+b'\0'
        body=rect(0,1920,0,1920)+struct.pack('<HH',30*256,1)+bitmap+shapes[56]+shapes[57]+b''.join(wrappers)+tag(56,exports)+tag(12,b'\0')+tag(1)+tag(0)
        (folder/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
        run='jinye-sampling-'+uuid.uuid4().hex[:12]
        script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('CLIPS',json.dumps(clips,separators=(',',':'))).replace('CASES',re.sub(r'"([A-Za-z_]+)":',r'\1:',json.dumps(cases,separators=(',',':'))))
        (folder/'scripts/frame_1/DoAction.as').write_text(script)
        subprocess.run(['java',f'-Duser.home={folder}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(folder/'base.swf'),str(folder/'game/main.swf'),str(folder/'scripts')],check=True,stdout=subprocess.DEVNULL)
        after={struct.unpack_from('<H',p)[0]:r for code,p,r in source_tags(folder/'game/main.swf') if code in (2,36) and struct.unpack_from('<H',p)[0] in (55,56,57)}
        assert after=={55:bitmap,**shapes}
        report={'run_id':run,'mode':mode,'source_graph':graph['source'],'changes':changes,
                'original_shape_sha256':{str(cid):hashlib.sha256(r).hexdigest() for cid,(_,r) in raw.items()},
                'shape_sha256':{str(cid):hashlib.sha256(r).hexdigest() for cid,r in shapes.items()},'lossless_tag_sha256':hashlib.sha256(bitmap).hexdigest(),
                'input_rgba_sha256':hashlib.sha256(bytes(c for p in rgba for c in p)).hexdigest(),'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),
                'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),
                'swf_sha256':hashlib.sha256((folder/'game/main.swf').read_bytes()).hexdigest(),'production_admitted':False}
        (folder/'build.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
    return reports


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();print(len(build(a.output,a.ffdec.resolve())))
