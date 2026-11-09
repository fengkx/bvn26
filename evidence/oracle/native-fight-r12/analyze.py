"""Validate marker shape only; no live or oracle acceptance in this offline slice."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent
KINDS=['startfight-entry','startfight-state-written','menu-write-before','menu-write-after','menu-exit','startfight-exit']


def validate_boundary(events):
    if [e['kind'] for e in events]!=KINDS:raise ValueError('Missing, reordered, duplicated or nested startFight/menu boundary')
    fields=[list(map(unquote,e['data'].split(','))) for e in events]
    if any(len(fields[i])!=6 for i in (0,1,5)) or any(len(fields[i])!=3 for i in (2,3,4)):raise ValueError('Malformed boundary fields')
    if fields[1][:2]!=['false','false']:raise ValueError('Readying/unpause writes not observed')
    if fields[2][0]!='true' or fields[3][:2]!=['true','true'] or fields[4][:2]!=['true','true']:raise ValueError('Menu requested/assigned/returned state mismatch')
    if fields[5][:3]!=['false','false','true']:raise ValueError('startFight exit state mismatch')
    return dict(source_boundary_shape_observed=True,production_admitted=False,native_parity_proven=False,oracle_accepted=False,certified_global_tick=False)


def replay():
    r09=HERE.parent/'native-fight-r09'
    spec=importlib.util.spec_from_file_location('r05',HERE.parent/'native-fight-r05/analyze.py');r05=importlib.util.module_from_spec(spec);spec.loader.exec_module(r05)
    build=json.loads((r09/'build.json').read_text());raw=(r09/'run-01/tagged.log').read_bytes()
    hashes=json.loads((r09/'artifact-sha256.json').read_text())
    for name in ['build.json','run-01/tagged.log']:
        if hashlib.sha256((r09/name).read_bytes()).hexdigest()!=hashes[name]:raise ValueError('Immutable receipt mismatch')
    rows=r05.base.parse(raw,build['run_id'])
    events=[r for r in rows if r['kind'] in KINDS]
    report=dict(production_admitted=False,native_parity_proven=False,oracle_accepted=False,new_live_runs=0,existing_r09_startfight_marker_count=len(events),input_sha256={n:hashes[n] for n in ['build.json','run-01/tagged.log']})
    try:validate_boundary(events)
    except ValueError as exc:report['marker_refusal']=str(exc)
    try:r05.validate_rows(raw,build)
    except ValueError as exc:report['original_structural_refusal']=str(exc)
    report['refusal']='No r12 live marker sequence; shape-only validation cannot admit a production oracle'
    (HERE/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-oracle',action='store_true');p.parse_args()
    print(json.dumps(replay(),indent=2))
    raise SystemExit(1)
