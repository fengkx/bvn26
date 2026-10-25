"""Capture unchanged smooth source leaves with explicit cache materialization controls."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import struct
import subprocess
import uuid
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_minimal_swf import rect,tag

HARNESS=Path('tools/probes/flash_filters/jinye-leaf-boundaries.as')


def matrix(values):
    return [round(float(values.get(k,default))*65536)/65536 for k,default in
            [('scaleX',1),('rotateSkew0',0),('rotateSkew1',0),('scaleY',1)]]+[int(values.get(k,0))/20 for k in ('translateX','translateY')]


def build(output,ffdec):
    inventory=ROOT/'evidence/importer-loud-fail/r220/inventory.json'
    graph=json.loads(inventory.read_text()); source=ROOT/graph['source']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==graph['source']['sha256']
    raw={struct.unpack_from('<H',p)[0]:(p,r) for code,p,r in source_tags(source) if code in (2,35) and struct.unpack_from('<H',p)[0] in (55,56,57)}
    assert set(raw)=={55,56,57}
    assert all(hashlib.sha256(r).hexdigest()==graph['raw_tag_sha256'][str(cid)] for cid,(_,r) in raw.items())
    cases=[];normal=graph['case']['normalization'];outer=matrix(graph['case']['placement']['matrix'])
    for frame in (1,10):
        placement=graph['graph']['frames'][frame-1]['placements'][0]
        assert placement['depth']==1 and placement['character_id']==(56 if frame==1 else 57)
        values=matrix(placement['matrix'])
        cases.append({'id':len(cases),'source_frame':frame,'shape':placement['character_id'],
                      'placement':placement,'matrix':values,'outer':outer,
                      'draw':[normal['scale'],0,0,normal['scale'],normal['x'],normal['y']]})
    output.mkdir(parents=True,exist_ok=True);(output/'game').mkdir(exist_ok=True);(output/'scripts/frame_1').mkdir(parents=True,exist_ok=True)
    wrappers=[];exports=struct.pack('<H',2)
    for cid in (56,57):
        wid=60000+cid-56
        wrapper=struct.pack('<HH',wid,1)+tag(26,b'\x06'+struct.pack('<HH',1,cid)+b'\0')+tag(1)+tag(0)
        wrappers.append(tag(39,wrapper));exports+=struct.pack('<H',wid)+f'leaf{cid}'.encode()+b'\0'
    body=rect(0,12000,0,8000)+struct.pack('<HH',30*256,1)+b''.join(raw[cid][1] for cid in (55,56,57))+b''.join(wrappers)+tag(56,exports)+tag(12,b'\0')+tag(1)+tag(0)
    (output/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
    run='jinye-leaf-'+uuid.uuid4().hex[:12]
    script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('CASES',re.sub(r'"([A-Za-z_]+)":',r'\1:',json.dumps([{k:v for k,v in c.items() if k != 'placement'} for c in cases],separators=(',',':'))))
    (output/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(output/'base.swf'),str(output/'game/main.swf'),str(output/'scripts')],check=True,stdout=subprocess.DEVNULL)
    after={struct.unpack_from('<H',p)[0]:r for code,p,r in source_tags(output/'game/main.swf') if code in (2,35) and struct.unpack_from('<H',p)[0] in raw}
    assert after=={cid:r for cid,(_,r) in raw.items()}
    fixture={'cases':cases,'shapes':graph['shapes'],'source':graph['source'],'raw_tag_sha256':{str(cid):hashlib.sha256(r).hexdigest() for cid,(_,r) in raw.items()},'production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
    report={'run_id':run,'source':graph['source'],'inventory_sha256':hashlib.sha256(inventory.read_bytes()).hexdigest(),'raw_tags_preserved':True,
            'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),
            'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'production_admitted':False}
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();print(build(a.output,a.ffdec.resolve())['run_id'])
