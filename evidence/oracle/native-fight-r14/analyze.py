"""Refuse OS/global-tick joins without synchronization or consumer observations."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent


def validate_consumer(events):
    kinds=[e['kind'] for e in events]
    if len(events)<2 or kinds[:2]!=['consumer-query-before','consumer-predicate-result']:raise ValueError('Missing consumer query/result')
    fields=[list(map(unquote,e['data'].split(','))) for e in events]
    if len(fields[0])!=6 or len(fields[1])!=4:raise ValueError('Malformed consumer identity')
    identity=fields[0][:3]
    if identity[2] not in ('doStand','doAllAction') or not identity[1].isdigit() or int(identity[1])<1:raise ValueError('Unknown site/local serial')
    if fields[1][:3]!=identity:raise ValueError('Consumer identity mismatch')
    result=fields[1][3]
    if result not in ('true','false'):raise ValueError('Nonboolean predicate result')
    expected=['consumer-query-before','consumer-predicate-result']+(['consumer-goto-before','consumer-goto-after'] if result=='true' else [])
    if kinds!=expected:raise ValueError('Missing, extra or reordered original goto boundary')
    for f in fields[2:]:
        if len(f)!=6 or f[:3]!=identity or f[3]!=fields[0][3]:raise ValueError('Goto owner/consumer mismatch')
    if any(f[5]!='false' for f in [fields[0]]+fields[2:]):raise ValueError('AI/unidentified branch is not physical-input consumption')
    return dict(predicate_result=result,source_interval_shape=True,certified_global_tick=False,os_input_join_proven=False,oracle_accepted=False)


def replay():
    r13=HERE.parent/'native-fight-r13'
    names=['build.json','run-01/tagged.log','run-01/session.json']
    hashes=json.loads((r13/'artifact-sha256.json').read_text())
    for name in names:
        if hashlib.sha256((r13/name).read_bytes()).hexdigest()!=hashes[name]:raise ValueError('Immutable receipt mismatch')
    spec=importlib.util.spec_from_file_location('r05',HERE.parent/'native-fight-r05/analyze.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    build=json.loads((r13/'build.json').read_text());session=json.loads((r13/'run-01/session.json').read_text());raw=(r13/'run-01/tagged.log').read_bytes()
    if session['observer_build']!=build:raise ValueError('Session/build mismatch')
    rows=old.base.parse(raw,build['run_id'])
    positives=[r for r in rows if r['kind']=='fight-key-return' and r['data'].split(',')[2]=='true']
    report=dict(production_admitted=False,native_parity_proven=False,oracle_accepted=False,certified_global_tick=False,os_input_join_proven=False,
                input_sha256={n:hashes[n] for n in names},physical_fight_operation=session['input_operations'][-1],positive_native_queries=positives,
                consumer_marker_count=sum(r['kind'].startswith('consumer-') for r in rows),
                clock_domains=dict(os='Python wall/monotonic command bracket, not per-edge dispatch/consumption',native='Flash getTimer plus camera-local ordinal',calibrated_mapping=None),
                refusal='No observed consumer interval or certified cross-clock/event join; temporal proximity is insufficient')
    try:old.validate_rows(raw,build)
    except ValueError as exc:report['original_structural_refusal']=str(exc)
    (HERE/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-oracle',action='store_true');p.parse_args()
    print(json.dumps(replay(),indent=2));raise SystemExit(1)
