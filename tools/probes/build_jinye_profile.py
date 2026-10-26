"""Profile only owned repeated draws of the pinned actual Jinye source leaf."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import uuid
from tools.probes.build_jinye_materialization import build as build_materialization
from tools.probes.build_bound_bitmap_component import ROOT,source_tags

HARNESS=Path('tools/probes/flash_filters/jinye-source-profile.as')
WORKLOADS=('direct_uncached','direct_cached_reuse','direct_cached_regenerate','local_uncached')


def build(output,ffdec,workload):
    assert workload in WORKLOADS;output=output.resolve();build_materialization(output,ffdec)
    fixture=json.loads((output/'fixture.json').read_text());fixture['profile_workload']=workload;fixture['minimum_duration_ms']=8000;fixture['draws_per_batch']=1000
    run='jinye-profile-'+uuid.uuid4().hex[:12];spec=fixture['cases'][0]
    js=lambda value:re.sub(r'"([A-Za-z_]+)":',r'\1:',json.dumps(value,separators=(',',':')))
    script=(ROOT/HARNESS).read_text().replace('RUN',run).replace('SPEC',js({k:spec[k] for k in ('id','shape','matrix','outer','draw')})).replace('ALLOCATION',js(fixture['local_allocation'])).replace('WORKLOAD',json.dumps(workload))
    (output/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(output/'base.swf'),str(output/'game/main.swf'),str(output/'scripts')],check=True,stdout=subprocess.DEVNULL)
    raw={str(struct.unpack_from('<H',p)[0]):hashlib.sha256(r).hexdigest() for c,p,r in source_tags(output/'game/main.swf') if c in (2,35)};assert raw==fixture['raw_tag_sha256']
    (output/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
    report={'run_id':run,'workload':workload,'fixture_sha256':hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),
            'source':fixture['source'],'raw_tags_preserved':True,'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'swf_sha256':hashlib.sha256((output/'game/main.swf').read_bytes()).hexdigest(),
            'profiling_proves_operands':False,'production_admitted':False}
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);p.add_argument('--workload',choices=WORKLOADS,required=True);a=p.parse_args();print(build(a.output,a.ffdec.resolve(),a.workload)['run_id'])
