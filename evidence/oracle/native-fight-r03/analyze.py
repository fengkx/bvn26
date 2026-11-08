"""Validate a run-tagged observation prefix without promoting it to a replay."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote


def parse(raw, run_id):
    rows = []
    for line in raw.splitlines():
        fields = line.decode('ascii').split('|', 7)
        if len(fields) != 8 or fields[:2] != ['M002', run_id]:
            raise ValueError('Foreign tag or malformed observation')
        _, _, seq, timer, ordinal, phase, kind, data = fields
        row = dict(seq=int(seq), timer_ms=int(timer), ordinal=int(ordinal), phase=phase, kind=kind, data=data)
        if row['seq'] != len(rows) + 1:
            raise ValueError('Sequence gap or duplicate')
        rows.append(row)
    if not rows or rows[0]['kind'] != 'boot' or sum(r['kind']=='boot' for r in rows) != 1:
        raise ValueError('Unique initial boot marker absent')
    return rows


def analyze(directory):
    session = json.loads((directory/'session.json').read_text())
    build = session['observer_build']
    run_id = build['run_id']
    prefix = ('M002|' + run_id + '|').encode()
    prelaunch = (directory/'flashlog.prelaunch.log').read_bytes()
    baseline = (directory/'flashlog.input-baseline.log').read_bytes()
    final = (directory/'flashlog.after.log').read_bytes()
    raw = (directory/'tagged.log').read_bytes()
    if prefix in prelaunch or not final.startswith(baseline):
        raise ValueError('Run-tag freshness or input interval append check failed')
    selected = b'\n'.join(line for line in final.splitlines() if line.startswith(prefix)) + b'\n'
    if selected != raw:
        raise ValueError('Selected tagged log does not match retained raw log')
    rows = parse(raw,run_id)
    pid = session['movie_pid']
    if session.get('remaining_movie_pids') or session.get('asset_recheck') != 'passed':
        raise ValueError('Cleanup or asset recheck incomplete')
    for operation in session['input_operations']:
        if operation['pid'] != pid or not operation.get('result','').startswith(str(pid)+', true,'):
            raise ValueError('Input operation did not return the owned PID')
    counts = Counter(r['kind'] for r in rows)
    entries = [r for r in rows if r['kind']=='game-state' and r['phase']=='game-entry']
    if not entries or [r['ordinal'] for r in entries] != list(range(1,len(entries)+1)):
        raise ValueError('Local callback entry coverage has gaps')
    first_running = next((r for r in entries if r['data'].split(',')[2:4] == ['false','false']),None)
    first_actors = [r for r in rows if first_running and r['ordinal']==first_running['ordinal'] and r['kind']=='actor-state' and r['phase']=='game-entry']
    keys = [r for r in rows if r['kind']=='key-return' and r['data'].endswith(',true')]
    randoms = [r for r in rows if r['kind']=='random-return']
    if not randoms or not keys or first_running is None or len(first_actors)!=2:
        raise ValueError('State/input/random live observations missing')
    for r in randoms:
        if not unquote(r['data'].split(',',1)[-1]).startswith('f:'):
            raise ValueError('Random sample is not retained binary significand encoding')
    report = {'kind':'native-observer-analysis','production_admitted':False,'native_parity_proven':False,'oracle_accepted':False,
              'run_tag':run_id,'movie_pid':pid,'events':len(rows),'counts':dict(counts),'local_callback_entries':len(entries),
              'tagged_sha256':hashlib.sha256(raw).hexdigest(),'fresh_tag_and_contiguous_sequence':True,
              'first_observed_unpaused_entry':first_running,'first_observed_unpaused_actors':first_actors,
              'positive_key_queries':len(keys),'positive_fight_ordinal_queries':sum(r['ordinal']>0 for r in keys),
              'first_positive_key_queries':keys[:12], 'random_samples':len(randoms),'first_random_samples':randoms[:5],
              'scope':'Observed forwarding returns and existing camera/wall-controller entry/exit. Local callback ordinal is NOT a proved global tick; key query is NOT downstream action consumption.',
              'attribution':'Fresh unique tag in one pinned build and one receipt-matched live movie PID; strict sequence and retained raw-log selection. Not an OS-level per-write PID attestation.',
              'unproved':['global clock/phase ordering','exact gameplay initial-state boundary','downstream input consumption','complete random consumer provenance','random replay','deterministic repeat','observer noninterference']}
    (directory/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    (directory/'random-observations.json').write_text(json.dumps({'kind':'observed-random-returns-not-replay-tape','run_tag':run_id,'samples':randoms},indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['events','counts','local_callback_entries','positive_fight_ordinal_queries','random_samples']}))
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--require-oracle',action='store_true')
    args=parser.parse_args()
    result=analyze(args.directory)
    raise SystemExit(1 if args.require_oracle and not result['oracle_accepted'] else 0)
