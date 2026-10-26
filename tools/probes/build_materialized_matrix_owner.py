"""Explicitly materialize original cache bytes before native ColorMatrix APIs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
from tools.probes.build_matrix_owner_family import build as family_build
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_nearest_component_input import decode
from tools.probes.analyze_affine_cache_support import bounds

HARNESS=Path('tools/probes/flash_filters/materialized-matrix-owner.as')


def build(output,ffdec):
    reports=family_build(ROOT/'evidence/importer-loud-fail/r32/components/main/cases.json',output,ffdec)
    report=reports[1];assert report['case']['id']=='main-298-3-1'
    fixture,_,cases=decode(ROOT/'evidence/importer-loud-fail/r179/native')
    allocation=bounds(['0']*3+['137','200']+cases[1]['key'][3:15],'separate')
    native=output.resolve()/'frame3/components/main';run='materialized-matrix-'+uuid.uuid4().hex[:12]
    script=(ROOT/HARNESS).read_text();normal=report['case']['normalization'];assert normal['scale']==1
    tokens={'RUN':run,'CASE_ID':report['case']['id'],'DRAW_X':normal['x'],'DRAW_Y':normal['y'],
            'CACHE_X':allocation[0],'CACHE_Y':allocation[1],'CACHE_WIDTH':allocation[2],'CACHE_HEIGHT':allocation[3]}
    for token,value in tokens.items():assert token in script;script=script.replace(token,str(value))
    (native/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output.resolve()}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(native/'base.swf'),str(native/'game/main.swf'),str(native/'scripts')],check=True,stdout=subprocess.DEVNULL)
    report.update({'run_id':run,'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),
                   'sample_ticks':[0,8],'cache_allocation':allocation,
                   'outputs_sha256':{'game/main.swf':hashlib.sha256((native/'game/main.swf').read_bytes()).hexdigest()}})
    (native/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True);a=p.parse_args();print(build(a.output,a.ffdec.resolve())['run_id'])
