"""Observe a readiness subset without certifying startFight or admission."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
R09=HERE.parent/'native-fight-r09'
spec=importlib.util.spec_from_file_location('r10',HERE.parent/'native-fight-r10/analyze.py')
r10=importlib.util.module_from_spec(spec);spec.loader.exec_module(r10)


def classify(rows):
    phases=r10.classify(rows)
    assigned=phases['hp_after']['marker']['seq']
    ready=[r for r in rows if r['kind']=='ready-play-before']
    if len(ready)!=1:raise ValueError('Absent/ambiguous ready-play marker; no phase inference')
    checkpoints=[]
    for index,row in enumerate(rows):
        if row['kind']!='game-state' or row['phase']!='game-entry':continue
        fields=row['data'].split(',')
        if len(fields)!=11 or any(fields[n] not in ('true','false') for n in (2,3,4)):
            raise ValueError('Malformed pause/loading state')
        actors,values=r10.actors_after(rows,index)
        checks=dict(after_observed_hp_assignment=row['seq']>assigned,
                    after_ready_play_request=row['seq']>ready[0]['seq'],
                    observed_unpaused=fields[2:4]==['false','false'],observed_p2loaded=fields[4]=='true',
                    actor_fields_complete=all(r10.NUMBER.fullmatch(v) for a in values for v in a[1:]))
        checkpoints.append(dict(marker=row,actors=actors,conditions=checks,observed_subset_satisfied=all(checks.values())))
    candidates=[c for c in checkpoints if c['observed_subset_satisfied']]
    first=candidates[0] if candidates else None
    previous=None
    if first:
        i=checkpoints.index(first)
        previous=checkpoints[i-1] if i else None
    timers=[]
    for boundary in phases['clock_boundaries']:
        row=boundary['boundary'];fields=row['data'].split(',')
        if len(fields)!=4 or any(v not in ('true','false') for v in fields[2:]):raise ValueError('Malformed timer pause flags')
        if row['seq']<assigned:
            label='pre-hp-incomplete' if not boundary['complete_fields'] else 'pre-hp-complete-not-initialized-proof'
        elif not boundary['complete_fields']:label='post-hp-incomplete'
        elif fields[2:]==['false','false']:label='post-hp-complete-unpaused-readiness-unproved'
        else:label='post-hp-complete-paused'
        timers.append(dict(**boundary,classification=label,
                           relation_to_first_subset_checkpoint='no-candidate' if first is None else 'before' if row['seq']<first['marker']['seq'] else 'at-or-after',
                           timer_readiness_proven=False))
    return dict(production_admitted=False,native_parity_proven=False,oracle_accepted=False,
                exact_fight_start_proven=False,full_fight_readiness_proven=False,
                first_observed_subset=first,preceding_game_entry=previous,ready_play_marker=ready[0],hp_assignment=phases['hp_after'],
                game_entry_count=len(checkpoints),subset_candidate_count=len(candidates),
                game_entries=[dict(marker=c["marker"],actor_sequences=[a["seq"] for a in c["actors"]],conditions=c["conditions"],observed_subset_satisfied=c["observed_subset_satisfied"]) for c in checkpoints],clock_boundaries=timers,timer_counts=dict(Counter(t['classification'] for t in timers)),
                missing_signals=['source-local startFight entry/normal-exit','readying=false observation','setMenuEnable(true) outcome','certified global scheduler tick','loaded instance continuity across boundaries'])


def replay():
    hashes=json.loads((R09/'artifact-sha256.json').read_text())
    names=['run-01/tagged.log','run-01/session.json','build.json','run-01/flashlog.prelaunch.log','run-01/flashlog.input-baseline.log','run-01/flashlog.after.log']
    for name in names:
        if hashlib.sha256((R09/name).read_bytes()).hexdigest()!=hashes[name]:raise ValueError('Immutable input mismatch')
    build=json.loads((R09/'build.json').read_text());session=json.loads((R09/'run-01/session.json').read_text())
    if session['observer_build']!=build:raise ValueError('Session/build mismatch')
    raw=(R09/'run-01/tagged.log').read_bytes();final=(R09/'run-01/flashlog.after.log').read_bytes();prefix=('M002|'+build['run_id']+'|').encode()
    if prefix in (R09/'run-01/flashlog.prelaunch.log').read_bytes() or not final.startswith((R09/'run-01/flashlog.input-baseline.log').read_bytes()):raise ValueError('Freshness/append mismatch')
    if b'\n'.join(l for l in final.splitlines() if l.startswith(prefix))+b'\n'!=raw:raise ValueError('Raw/tag selection mismatch')
    rows=r10.r05.base.parse(raw,build['run_id'])
    report=classify(rows)
    try:r10.r05.validate_rows(raw,build);report['original_structural_refusal']=None
    except ValueError as exc:report['original_structural_refusal']=str(exc)
    source_sha=hashlib.sha256((ROOT/'scripts/main.json').read_bytes()).hexdigest()
    if source_sha!=build['source_sha256']['scripts/main.json']:raise ValueError('Source hash mismatch')
    report.update(input_sha256={n:hashes[n] for n in names},source_sha256=source_sha,events_retained=len(rows),
                  scope='Readiness subset at sampled game entry only; not exact startFight, global tick, or complete oracle')
    (HERE/'classification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--require-oracle',action='store_true');p.parse_args()
    try:
        r=replay();print(json.dumps(dict(timer_counts=r['timer_counts'],first_subset_seq=r['first_observed_subset']['marker']['seq'] if r['first_observed_subset'] else None,original_structural_refusal=r['original_structural_refusal'],oracle_accepted=False)))
    except (ValueError,KeyError,OSError) as exc:print('Refused: '+str(exc))
    raise SystemExit(1)
