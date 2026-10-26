"""Capture a pinned Glow component with complete native filter property readbacks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT=Path(__file__).resolve().parents[2]
HARNESS=Path('tools/probes/flash_filters/component-glow-boundaries.as')


def build(cases_path,case_id,output,ffdec):
    output=output.resolve()
    if any(p==output or p in output.parents for p in (ROOT/'game',ROOT/'scripts')):raise ValueError('Locked input output path')
    cases=json.loads(cases_path.read_text());matches=[c for c in cases if c['id']==case_id]
    if len(matches)!=1:raise ValueError('Missing/ambiguous pinned component')
    case=matches[0]
    assert case['source_frame_count']==case['frame_count']==1
    assert hashlib.sha256((ROOT/case['source']['path']).read_bytes()).hexdigest()==case['source']['sha256']
    assert len(case['placement']['filters'])==1 and case['placement']['filters'][0]['type']=='GLOWFILTER'
    output.mkdir(parents=True,exist_ok=True)
    (output/'inventory.json').write_text(json.dumps([{k:v for k,v in case.items() if k not in ('normalization','samples','wrapper_symbol')}])+'\n')
    env={**os.environ,'BVN_REVIEW_DIR':str(output),'BVN_FFDEC':str(ffdec),'JAVA_TOOL_OPTIONS':f'-Duser.home={output}'}
    subprocess.run(['python3',str(ROOT/'evidence/characters/pain/visual-parity/review/probes/build_components.py')],cwd=ROOT,env=env,check=True,stdout=subprocess.DEVNULL)
    native=output/'components'/Path(case['source']['path']).stem
    run='component-glow-'+uuid.uuid4().hex[:12]
    script=(ROOT/HARNESS).read_text();values={'RUN':run,'DEPTH':case['placement']['depth'],'SCALE':case['normalization']['scale'],'ORIGIN_X':case['normalization']['x'],'ORIGIN_Y':case['normalization']['y']}
    for token,value in values.items():assert token in script;script=script.replace(token,str(value))
    (native/'scripts/frame_1/DoAction.as').write_text(script)
    subprocess.run(['java',f'-Duser.home={output}','-Djava.awt.headless=true','-jar',str(ffdec),'-importScript',str(native/'base.swf'),str(native/'game/main.swf'),str(native/'scripts')],check=True,stdout=subprocess.DEVNULL)
    report={'run_id':run,'case':case,'source':case['source']['path'],'source_sha256':case['source']['sha256'],'harness_source':str(HARNESS),'harness_sha256':hashlib.sha256((ROOT/HARNESS).read_bytes()).hexdigest(),'outputs_sha256':{'game/main.swf':hashlib.sha256((native/'game/main.swf').read_bytes()).hexdigest()},'ffdec_sha256':hashlib.sha256(ffdec.read_bytes()).hexdigest(),'production_admitted':False}
    (native/'build.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cases',type=Path,required=True);p.add_argument('--case',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffdec',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.cases,a.case,a.output,a.ffdec.resolve()),indent=2))
