"""Vary draw clip rectangles without moving the source or destination geometry."""
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
from tools.probes.decode_jinye_affine_controls import source_pixel

HARNESS=Path('tools/probes/flash_filters/jinye-clip-controls.as')


def controls():
    graph,old=old_controls()
    cases=[{**c,'id':i,'base_case':c['id']} for i,c in enumerate(c for c in old if c['draw'][0]!=2)]
    clips=[None,[0,0,96,96]]+[[left,0,width,96] for left in (46,47,48) for width in (1,3,4,5,16)]
    assert len(cases)==24 and len(clips)==17
    return graph,cases,clips


def build(output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    graph,cases,clips=controls();pinned={'cases':cases,'clips':clips,'source_graph':graph,'size':[96,96],'source_size':[92,40],'production_admitted':False}
    raw={struct.unpack_from('<H',p)[0]:r for code,p,r in source_tags(ROOT/graph['source']['path']) if code==2 and struct.unpack_from('<H',p)[0] in (56,57)}
    assert set(raw)=={56,57} and all(hashlib.sha256(r).hexdigest()==graph['raw_tag_sha256'][str(cid)] for cid,r in raw.items())
    output.mkdir(parents=True,exist_ok=True);(output/'fixture.json').write_text(json.dumps(pinned,indent=2)+'\n');reports=[]
    for source in range(6):
        folder=output/f'source{source}';(folder/'game').mkdir(parents=True,exist_ok=True);(folder/'scripts/frame_1').mkdir(parents=True,exist_ok=True)
        rgba=[source_pixel(source,x,y) for y in range(40) for x in range(92)]
        argb=bytes(c for r,g,b,a in rgba for c in (a,r,g,b))
        payload=struct.pack('<HBHH',55,5,92,40)+zlib.compress(argb)
        # Bitmap tags retain long headers even when an impulse compresses below 63 bytes.
        bitmap=struct.pack('<HI',(36<<6)|63,len(payload))+payload
        wrappers=[];exports=struct.pack('<H',3)+struct.pack('<H',55)+b'sourceBitmap\0'
        for cid in (56,57):
            wid=60000+cid-56
            wrappers.append(tag(39,struct.pack('<HH',wid,1)+tag(26,b'\x06'+struct.pack('<HH',1,cid)+b'\0')+tag(1)+tag(0)))
            exports+=struct.pack('<H',wid)+f'leaf{cid}'.encode()+b'\0'
        body=rect(0,1920,0,1920)+struct.pack('<HH',30*256,1)+bitmap+raw[56]+raw[57]+b''.join(wrappers)+tag(56,exports)+tag(12,b'\0')+tag(1)+tag(0)
        (folder/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
        subset=[c for c in cases if c['source']==source];assert len(subset)==4
        run='jinye-clip-'+uuid.uuid4().hex[:12]
        script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('SOURCE_ID',str(source)).replace('CLIPS',json.dumps(clips,separators=(',',':'))).replace('CASES',re.sub(r'"([A-Za-z_]+)":',r'\1:',json.dumps(subset,separators=(',',':'))))
        (folder/'scripts/frame_1/DoAction.as').write_text(script)
        subprocess.run(['java',f'-Duser.home={folder}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(folder/'base.swf'),str(folder/'game/main.swf'),str(folder/'scripts')],check=True,stdout=subprocess.DEVNULL)
        after={struct.unpack_from('<H',p)[0]:r for code,p,r in source_tags(folder/'game/main.swf') if code in (2,36) and struct.unpack_from('<H',p)[0] in (55,56,57)}
        assert after=={55:bitmap,**raw}
        report={'run_id':run,'source_id':source,'case_ids':[c['id'] for c in subset],'native_api':'original DefineShape fill65 + DefineBitsLossless2',
                'source_graph':graph['source'],'raw_shape_sha256':{str(cid):hashlib.sha256(r).hexdigest() for cid,r in raw.items()},
                'lossless_tag_sha256':hashlib.sha256(bitmap).hexdigest(),'input_rgba_sha256':hashlib.sha256(bytes(c for p in rgba for c in p)).hexdigest(),
                'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),
                'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),
                'swf_sha256':hashlib.sha256((folder/'game/main.swf').read_bytes()).hexdigest(),'production_admitted':False}
        (folder/'build.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
    return reports


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();print(len(build(a.output,a.ffdec.resolve())))
