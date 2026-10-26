"""Compare original SWF-tag shape with AS fill construction from identical pinned source bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
from tools.probes.build_animated_component_boundaries import build as animated_build
from tools.probes.build_bound_bitmap_component import ROOT

HARNESS=Path('tools/probes/flash_filters/component-fill-api.as')


def build(output,ffdec):
    fixture_path=ROOT/'evidence/importer-loud-fail/r142/fixture.json';f=json.loads(fixture_path.read_text());leaf=f['leaves']['8'];case=f['case']
    report=animated_build(ROOT/'evidence/importer-loud-fail/r21/components/lanran/cases.json',case['id'],output,ffdec)
    assert case==report['case'];native=output.resolve()/'components/lanran';raw=leaf['pixels_premultiplied']
    assert all(p[3] in (0,255) and (p[3]!=0 or p[:3]==[0,0,0]) for p in raw),'Unproven setPixel32 source roundtrip'
    run='fill-api-'+uuid.uuid4().hex[:12]
    values={'RUN':run,'SOURCE_BYTES':json.dumps([(a<<24)|(r<<16)|(g<<8)|b for r,g,b,a in raw],separators=(',',':')),'SOURCE_WIDTH':leaf['width'],'SOURCE_HEIGHT':leaf['height'],'SOURCE_CONTOUR':json.dumps(leaf['fill_masks'][0][0]),'FILL_X':float(leaf['fill_matrix']['translateX'])/20,'FILL_Y':float(leaf['fill_matrix']['translateY'])/20,'DEPTH':case['placement']['depth'],'SCALE':case['normalization']['scale'],'ORIGIN_X':case['normalization']['x'],'ORIGIN_Y':case['normalization']['y']}
    script=(ROOT/HARNESS).read_text()
    for token,value in values.items():assert token in script;script=script.replace(token,str(value))
    (native/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output.resolve()}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(native/'base.swf'),str(native/'game/main.swf'),str(native/'scripts')],check=True,stdout=subprocess.DEVNULL)
    report.update({'run_id':run,'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),'fixture_source':str(fixture_path.relative_to(ROOT)),'fixture_sha256':hashlib.sha256(fixture_path.read_bytes()).hexdigest(),'outputs_sha256':{'game/main.swf':hashlib.sha256((native/'game/main.swf').read_bytes()).hexdigest()}})
    (native/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();r=build(a.output.resolve(),a.ffdec.resolve());print(r['run_id'])
