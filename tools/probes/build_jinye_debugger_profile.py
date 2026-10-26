"""Build an independently hashed, longer owned-debugger feasibility workload."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import struct
from tools.probes.build_jinye_profile import build as profile_build
from tools.probes.build_bound_bitmap_component import ROOT,source_tags

HARNESS=Path('tools/probes/flash_filters/jinye-debugger-profile.as')


def build(output,ffdec,duration_ms=20000):
    assert duration_ms in (20000,60000)
    output=output.resolve();report=profile_build(output,ffdec,'direct_uncached')
    source=ROOT/'tools/probes/flash_filters/jinye-source-profile.as'
    assert (ROOT/HARNESS).read_text()==source.read_text().replace('>=8000','>=20000')
    script=output/'scripts/frame_1/DoAction.as';text=script.read_text();assert text.count('>=8000')==1
    script.write_text(text.replace('>=8000',f'>={duration_ms}'))
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(output/'base.swf'),str(output/'game/main.swf'),str(output/'scripts')],check=True,stdout=subprocess.DEVNULL)
    fixture=json.loads((output/'fixture.json').read_text());fixture['minimum_duration_ms']=duration_ms
    raw={str(struct.unpack_from('<H',p)[0]):hashlib.sha256(r).hexdigest() for c,p,r in source_tags(output/'game/main.swf') if c in (2,35)}
    assert raw==fixture['raw_tag_sha256']
    (output/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
    report.update(fixture_sha256=hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),harness_source=str(HARNESS),
                  harness_sha256=hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),swf_sha256=hashlib.sha256((output/'game/main.swf').read_bytes()).hexdigest(),instrumented_pixel_reference=False,raw_tags_after_final_import=raw,generated_script_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),duration_ms=duration_ms)
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--ffdec',type=Path,required=True);parser.add_argument('--duration-ms',type=int,choices=(20000,60000),default=20000);args=parser.parse_args();print(build(args.output,args.ffdec.resolve(),args.duration_ms)['run_id'])
