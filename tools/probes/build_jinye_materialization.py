"""Capture the actual first Jinye leaf before and after explicit bitmap materialization."""
import argparse
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import uuid
from tools.probes.build_jinye_leaf_boundaries import build as build_leaf
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_minimal_swf import tag
from tools.probes.analyze_jinye_smooth_leaf import source_geometry

HARNESS=Path('tools/probes/flash_filters/jinye-materialization.as')


def allocation_for(spec,shape):
    _,polygon=source_geometry({**spec,'outer':[1,0,0,1,0,0],'draw':[1,0,0,1,0,0]},shape)
    x=math.floor(min(p[0] for p in polygon))-1;y=math.floor(min(p[1] for p in polygon))-1
    w=math.ceil(max(p[0] for p in polygon))+1-x;h=math.ceil(max(p[1] for p in polygon))+1-y
    assert all(x<=p[0]<x+w and y<=p[1]<y+h for p in polygon)
    return [x,y,w,h],polygon


def build(output,ffdec):
    output=output.resolve();build_leaf(output,ffdec)
    fixture=json.loads((output/'fixture.json').read_text());spec=fixture['cases'][0]
    shape=next(s for s in fixture['shapes'] if s['id']==56)
    (x,y,w,h),polygon=allocation_for(spec,shape)
    fixture.update(cases=[spec],local_allocation=[x,y,w,h],allocation_rule='source_child_polygon_floor_ceil_plus_one',
                   local_polygon=[[str(v) for v in p] for p in polygon],materialized_attach={'pixel_snapping':'never','smoothing':True},
                   materialization_equals_native_cache=False)
    assert all(x<=p[0]<x+w and y<=p[1]<y+h for p in polygon)
    base=output/'base.swf';data=base.read_bytes();payload,raw=next((p,r) for c,p,r in source_tags(base) if c==56)
    count=struct.unpack_from('<H',payload)[0];updated=tag(56,struct.pack('<H',count+1)+payload[2:]+struct.pack('<H',55)+b'sourceBitmap\0')
    assert data.count(raw)==1;data=data.replace(raw,updated);data=data[:4]+struct.pack('<I',len(data))+data[8:];base.write_bytes(data)
    run='jinye-materialize-'+uuid.uuid4().hex[:12]
    js=lambda value:re.sub(r'"([A-Za-z_]+)":',r'\1:',json.dumps(value,separators=(',',':')))
    script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('SPEC',js({k:spec[k] for k in ('id','shape','matrix','outer','draw')})).replace('ALLOCATION',js([x,y,w,h]))
    (output/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(base),str(output/'game/main.swf'),str(output/'scripts')],check=True,stdout=subprocess.DEVNULL)
    after={str(struct.unpack_from('<H',p)[0]):hashlib.sha256(r).hexdigest() for c,p,r in source_tags(output/'game/main.swf') if c in (2,35)}
    assert after==fixture['raw_tag_sha256']
    (output/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
    report={'run_id':run,'source':fixture['source'],'raw_tags_preserved':True,'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),
            'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),
            'swf_sha256':hashlib.sha256((output/'game/main.swf').read_bytes()).hexdigest(),'production_admitted':False}
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();print(build(a.output,a.ffdec.resolve())['run_id'])
