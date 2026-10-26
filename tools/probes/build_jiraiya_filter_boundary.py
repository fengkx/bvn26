"""Observe authored wrapper filter mutation and explicit materialization boundaries."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid
from tools.probes.analyze_jiraiya_bitmap_binding import ROOT


def build(output,ffdec,harness=Path("tools/probes/flash_filters/jiraiya-filter-boundary.as")):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/"game",ROOT/"scripts")):
        raise ValueError("Locked inputs cannot be probe output")
    output.mkdir(parents=True,exist_ok=True)
    case=json.loads((ROOT/'evidence/importer-loud-fail/r21/components/jiraiya/cases.json').read_text())[0]
    inventory=[{k:v for k,v in case.items() if k not in ('normalization','samples','wrapper_symbol')}]
    (output/'inventory.json').write_text(json.dumps(inventory)+'\n')
    env={**os.environ,'BVN_REVIEW_DIR':str(output),'BVN_FFDEC':str(ffdec),'JAVA_TOOL_OPTIONS':f'-Duser.home={output}'}
    subprocess.run(['python3',str(ROOT/'evidence/characters/pain/visual-parity/review/probes/build_components.py')],cwd=ROOT,env=env,check=True,stdout=subprocess.DEVNULL)
    native=output/'components/jiraiya';run=harness.stem+'-'+uuid.uuid4().hex[:12]
    script=(ROOT/harness).read_text().replace('RUN',run)
    (native/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(native/'base.swf'),str(native/'game/main.swf'),str(native/'scripts')],check=True,stdout=subprocess.DEVNULL)
    report={'run_id':run,'source':case['source']['path'],'source_sha256':case['source']['sha256'],'harness_source':str(harness),'harness_sha256':hashlib.sha256((ROOT/harness).read_bytes()).hexdigest(),'outputs_sha256':{'game/main.swf':hashlib.sha256((native/'game/main.swf').read_bytes()).hexdigest()},'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'production_admitted':False}
    (native/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True)
    p.add_argument('--harness',type=Path,default=Path('tools/probes/flash_filters/jiraiya-filter-boundary.as'))
    a=p.parse_args();print(json.dumps(build(a.output,a.ffdec.resolve(),a.harness),indent=2))
