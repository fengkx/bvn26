"""Independent ramps/impulses retain the original Jinye affine fill geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import uuid
import xml.etree.ElementTree as ET
from tools.probes.build_bound_bitmap_component import ROOT,bitmap_shape_fill_polygons
from tools.probes.build_minimal_swf import rect,tag
from tools.probes.build_jinye_leaf_boundaries import matrix

HARNESS=Path('tools/probes/flash_filters/jinye-affine-controls.as')


def point(m,p):
    a,b,c,d,x,y=m;return [a*p[0]+c*p[1]+x,b*p[0]+d*p[1]+y]


def controls():
    fixture=json.loads((ROOT/'evidence/importer-loud-fail/r221/native/fixture.json').read_text())
    assert hashlib.sha256((ROOT/fixture['source']['path']).read_bytes()).hexdigest()==fixture['source']['sha256']
    shapes={s['id']:s for s in fixture['shapes']};cases=[]
    for original in fixture['cases']:
        shape=shapes[original['shape']];assert shape['fill_type']==65
        fill=matrix(shape['bitmap_matrix']);fill[:4]=[v/20 for v in fill[:4]]
        mask=bitmap_shape_fill_polygons(ET.fromstring(shape['xml']))[shape['active_fill']-1][0]
        center=point(original['outer'],point(original['matrix'],point(fill,[46,20])))
        for scale in (original['draw'][0],1,2):
            for source in range(6):
                cases.append({'id':len(cases),'shape':shape['id'],'source_frame':original['source_frame'],
                              'source':source,'fill':fill,'mask':mask,'matrix':original['matrix'],'outer':original['outer'],
                              'draw':[scale,0,0,scale,48-scale*center[0],48-scale*center[1]]})
    return fixture,cases


def build(output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    fixture,cases=controls();output.mkdir(parents=True,exist_ok=True);(output/'game').mkdir(exist_ok=True);(output/'scripts/frame_1').mkdir(parents=True,exist_ok=True)
    run='jinye-affine-'+uuid.uuid4().hex[:12]
    script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('CASES',re.sub(r'"([A-Za-z_]+)":',r'\1:',json.dumps(cases,separators=(',',':'))))
    (output/'scripts/frame_1/DoAction.as').write_text(script)
    body=rect(0,1920,0,1920)+struct.pack('<HH',30*256,1)+tag(12,b'\0')+tag(1)+tag(0)
    (output/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I',len(body)+8)+body)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(output/'base.swf'),str(output/'game/main.swf'),str(output/'scripts')],check=True,stdout=subprocess.DEVNULL)
    data={'cases':cases,'source_graph':fixture,'size':[96,96],'source_size':[92,40],'production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(data,indent=2)+'\n')
    report={'native_api':'Drawing API beginBitmapFill','source_tag_equivalence_proved':False,'run_id':run,'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),
            'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),
            'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'production_admitted':False}
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();print(build(a.output,a.ffdec.resolve())['run_id'])
