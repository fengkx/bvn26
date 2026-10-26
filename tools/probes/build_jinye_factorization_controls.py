"""Predeclared exact factorization pairs preserve total affine mapping and stage mask."""
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
from tools.probes.build_jinye_sampling_modes import source_pixel
from tools.probes.analyze_jinye_smooth_leaf import compose,invert,transform
from tools.probes.jinye_factorization_tags import encode_shape,parse_shape

HARNESS=Path('tools/probes/flash_filters/jinye-factorization-controls.as')


def controls():
    factors=[[1,0,0,1,0,0],[1,0,2,1,0,0],[1,0,-2,1,0,0],[1,2,0,1,0,0],[1,-2,0,1,0,0]]
    displays=[[1,0,.5,1,0,0],[1,.5,0,1,0,0]];mask=[[0,0],[92,0],[92,40],[0,40]]
    shapes=[];cases=[]
    for index,factor in enumerate(factors):
        raw=encode_shape(56+index,factor,[transform(factor,p) for p in mask]);parsed=parse_shape(raw)
        assert parsed['fill']==factor and parsed['mask']==[list(transform(factor,p)) for p in mask]
        shapes.append({'factor_id':index,'factor':factor,'raw_tag_hex':raw.hex(),'raw_tag_sha256':hashlib.sha256(raw).hexdigest(),'parsed':parsed})
    for display_id,display in enumerate(displays):
        for scale in (1,.5):
            for index,factor in enumerate(factors):
                child=compose(display,invert(factor));draw=[scale,0,0,scale,48,48]
                parsed=shapes[index]['parsed'];total=compose(draw,compose(child,parsed['fill']))
                polygon=[list(transform(compose(draw,child),p)) for p in parsed['mask']]
                assert total==compose(draw,display)
                assert polygon==[list(transform(compose(draw,display),p)) for p in mask]
                cases.append({'id':len(cases),'display_id':display_id,'factor_id':index,'shape':56+index,'matrix':child,
                              'outer':[1,0,0,1,0,0],'draw':draw,'expected_total':total,'expected_stage_mask':polygon})
    return {'cases':cases,'shapes':shapes,'source_size':[92,40],'size':[192,192],'production_admitted':False}


def build(output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    fixture=controls();output.mkdir(parents=True,exist_ok=True);(output/'game').mkdir(exist_ok=True);(output/'scripts/frame_1').mkdir(parents=True,exist_ok=True)
    (output/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
    rgba=[source_pixel(x,y) for y in range(40) for x in range(92)]
    payload=struct.pack('<HBHH',55,5,92,40)+zlib.compress(bytes(c for r,g,b,a in rgba for c in (a,r,g,b)))
    bitmap=struct.pack('<HI',(36<<6)|63,len(payload))+payload
    wrappers=[];exports=struct.pack('<H',6)+struct.pack('<H',55)+b'sourceBitmap\0';shapes={s['parsed']['shape']:bytes.fromhex(s['raw_tag_hex']) for s in fixture['shapes']}
    for cid in shapes:
        wid=60000+cid-56;wrappers.append(tag(39,struct.pack('<HH',wid,1)+tag(26,b'\x06'+struct.pack('<HH',1,cid)+b'\0')+tag(1)+tag(0)))
        exports+=struct.pack('<H',wid)+f'leaf{cid}'.encode()+b'\0'
    body=rect(0,3840,0,3840)+struct.pack('<HH',30*256,1)+bitmap+b''.join(shapes.values())+b''.join(wrappers)+tag(56,exports)+tag(12,b'\0')+tag(1)+tag(0)
    (output/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
    run='jinye-factor-'+uuid.uuid4().hex[:12]
    runtime=[{k:c[k] for k in ('id','shape','matrix','outer','draw')} for c in fixture['cases']]
    script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('CLIPS','[null]').replace('CASES',re.sub(r'"([A-Za-z_]+)":',r'\1:',json.dumps(runtime,separators=(',',':'))))
    (output/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(output/'base.swf'),str(output/'game/main.swf'),str(output/'scripts')],check=True,stdout=subprocess.DEVNULL)
    after={struct.unpack_from('<H',p)[0]:r for code,p,r in source_tags(output/'game/main.swf') if code in (2,36) and struct.unpack_from('<H',p)[0] in (55,*shapes)}
    assert after=={55:bitmap,**shapes}
    report={'run_id':run,'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),
            'raw_tags_unchanged_by_import':True,'shape_sha256':{str(cid):hashlib.sha256(raw).hexdigest() for cid,raw in shapes.items()},
            'lossless_tag_sha256':hashlib.sha256(bitmap).hexdigest(),'input_rgba_sha256':hashlib.sha256(bytes(c for p in rgba for c in p)).hexdigest(),
            'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),
            'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'swf_sha256':hashlib.sha256((output/'game/main.swf').read_bytes()).hexdigest(),'production_admitted':False}
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();print(build(a.output,a.ffdec.resolve())['run_id'])
