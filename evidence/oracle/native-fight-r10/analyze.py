"""Classify immutable rejected clock boundaries; never admit an oracle."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
R09=HERE.parent/'native-fight-r09'
spec=importlib.util.spec_from_file_location('r05',HERE.parent/'native-fight-r05/analyze.py')
r05=importlib.util.module_from_spec(spec);spec.loader.exec_module(r05)
FIELDS=['slot','x','y','xscale','bodyframe','hp','ql','action','beida','kcplayed']
NUMBER=re.compile(r'f:-?1:-?\d+:\d+:\d+')


def actors_after(rows,index):
    actors=rows[index+1:index+3]
    if len(actors)!=2 or any(a['kind']!='actor-state' for a in actors):raise ValueError('Missing immediate actor pair')
    values=[list(map(unquote,a['data'].split(','))) for a in actors]
    if any(len(v)!=len(FIELDS) for v in values) or [v[0] for v in values]!=['p1','p2']:raise ValueError('Malformed actor pair')
    return actors,values


def classify(rows):
    before=[i for i,r in enumerate(rows) if r['kind']=='chushi-hp-before']
    after=[i for i,r in enumerate(rows) if r['kind']=='chushi-hp-after']
    if len(before)!=1 or len(after)!=1 or after[0]!=before[0]+3:raise ValueError('HP boundary absent, duplicated or interleaved')
    bi,ai=before[0],after[0]
    before_actors,before_values=actors_after(rows,bi)
    after_actors,after_values=actors_after(rows,ai)
    expected=unquote(rows[ai]['data'].split(',')[0])
    if not NUMBER.fullmatch(expected) or any(v[5]!=expected for v in after_values):raise ValueError('HP after assignment is incomplete or differs from observed maxhp')
    unpaused=next((r for r in rows if r['kind']=='game-state' and r['phase']=='game-entry' and r['data'].split(',')[2:4]==['false','false']),None)
    result=[];pending=None;ordinal=0
    for i,row in enumerate(rows):
        if row['kind'] not in ('clock-entry','clock-exit'):continue
        clock=row['data'].split(',');number=int(clock[0])
        if len(clock)!=4:raise ValueError('Malformed clock data')
        if row['kind']=='clock-entry':
            if pending is not None or number!=ordinal+1:raise ValueError('Clock entry gap/nesting')
            pending=number
        else:
            if pending is None or number!=pending:raise ValueError('Unmatched clock exit')
            ordinal=number;pending=None
        actors,values=actors_after(rows,i)
        missing=[dict(actor=v[0],field=FIELDS[j],raw_value=v[j]) for v in values for j in range(1,len(v)) if not NUMBER.fullmatch(v[j])]
        phase='before-observed-hp-assignment' if i<bi else 'after-observed-hp-assignment' if i>ai else 'inside-hp-boundary'
        readiness='before-first-observed-unpaused-checkpoint' if unpaused is None or row['seq']<unpaused['seq'] else 'at-or-after-first-observed-unpaused-checkpoint'
        result.append(dict(boundary=row,actors=actors,phase=phase,readiness=readiness,complete_fields=not missing,missing=missing))
    if pending is not None or not result:raise ValueError('Missing/truncated timer coverage')
    return dict(hp_before=dict(marker=rows[bi],actors=before_actors),hp_after=dict(marker=rows[ai],actors=after_actors),first_observed_unpaused=unpaused,
                clock_boundaries=result,counts=dict(Counter(f'{r["phase"]}/{"complete" if r["complete_fields"] else "incomplete"}' for r in result)),
                readiness_counts=dict(Counter(r['readiness'] for r in result)),
                post_assignment_incomplete=sum(not r['complete_fields'] and r['phase']=='after-observed-hp-assignment' for r in result),
                production_admitted=False,native_parity_proven=False,oracle_accepted=False)


def replay():
    hashes=json.loads((R09/'artifact-sha256.json').read_text())
    names=['run-01/tagged.log','run-01/session.json','build.json','run-01/flashlog.prelaunch.log','run-01/flashlog.input-baseline.log','run-01/flashlog.after.log']
    for name in names:
        if hashlib.sha256((R09/name).read_bytes()).hexdigest()!=hashes[name]:raise ValueError('Immutable receipt hash mismatch: '+name)
    build=json.loads((R09/'build.json').read_text());session=json.loads((R09/'run-01/session.json').read_text())
    if session['observer_build']!=build:raise ValueError('Build identity mismatch')
    prefix=('M002|'+build['run_id']+'|').encode()
    final=(R09/'run-01/flashlog.after.log').read_bytes();raw=(R09/'run-01/tagged.log').read_bytes()
    if prefix in (R09/'run-01/flashlog.prelaunch.log').read_bytes() or not final.startswith((R09/'run-01/flashlog.input-baseline.log').read_bytes()):raise ValueError('Freshness/append mismatch')
    if b'\n'.join(l for l in final.splitlines() if l.startswith(prefix))+b'\n'!=raw:raise ValueError('Raw selection mismatch')
    rows=r05.base.parse(raw,build['run_id'])
    report=classify(rows)
    try:
        r05.validate_rows(raw,build)
        report['original_structural_refusal']=None
    except ValueError as exc:report['original_structural_refusal']=str(exc)
    report.update(kind='rejected-prefix-phase-classification-not-acceptance',input_sha256={n:hashes[n] for n in names},events_retained=len(rows),boundaries_retained=len(report['clock_boundaries']),
                  refusal='Full prefix remains unaccepted; phase classification does not certify initial state/global tick or permit incomplete fields',
                  source_sha256=hashlib.sha256((ROOT/'scripts/main.json').read_bytes()).hexdigest())
    if report['source_sha256']!=build['source_sha256']['scripts/main.json']:raise ValueError('Locked source mismatch')
    (HERE/'classification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-oracle',action='store_true');p.parse_args()
    try:
        r=replay();print(json.dumps({k:r[k] for k in ['counts','readiness_counts','post_assignment_incomplete','original_structural_refusal','oracle_accepted']}))
    except (ValueError,KeyError,OSError) as exc:print('Refused: '+str(exc))
    raise SystemExit(1)
