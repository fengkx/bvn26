"""Refuse unsupported live, initial-state and global-tick claims."""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('r03_analysis', HERE.parent/'native-fight-r03/analyze.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def validate_rows(raw, build):
    rows = base.parse(raw, build['run_id'])
    if any(r['timer_ms'] < 0 or r['ordinal'] < 0 for r in rows) or any(a['timer_ms'] > b['timer_ms'] for a,b in zip(rows,rows[1:])):
        raise ValueError('Timer regression/invalid ordinal; wrap requires explicit treatment')
    sites = {s['site'] for s in build['fight_sites']}
    callback = None
    callbacks = 0
    for row in rows:
        if row['kind']=='game-state':
            if row['phase']=='game-entry':
                if callback is not None or row['ordinal']!=callbacks+1:
                    raise ValueError('Camera callback entry gap/nesting')
                callback=row['ordinal']
            elif row['phase']=='game-exit':
                if callback is None or row['ordinal']!=callback:
                    raise ValueError('Camera callback exit unmatched')
                callbacks+=1
                callback=None
            else:
                raise ValueError('Unknown game-state phase')
    if callback is not None:
        raise ValueError('Camera callback truncated')
    keys = []
    clock = None
    clock_count = 0
    for index, row in enumerate(rows):
        if row['kind'] == 'fight-key-return':
            fields = row['data'].split(',')
            if len(fields)!=10 or fields[0] not in sites or fields[2] not in ('true','false'):
                raise ValueError('Unknown/malformed fight query site')
            if not fields[1].isdigit() or not unquote(fields[3]).startswith('/game/p1/'):
                raise ValueError('Fight key code/owner provenance missing')
            if fields[4:7] != ['false','false','false']:
                continue
            if not fields[7].isdigit() or any(not re.fullmatch(r'f:-?1:-?\d+:\d+:\d+', unquote(f)) for f in fields[8:]):
                raise ValueError('Fight state unavailable')
            keys.append(row)
        if row['kind'] in ('clock-entry','clock-exit'):
            fields = row['data'].split(',')
            if len(fields)!=4 or not fields[0].isdigit() or not unquote(fields[1]).startswith('f:'):
                raise ValueError('Clock state missing')
            number = int(fields[0])
            if row['kind']=='clock-entry':
                if clock is not None or number!=clock_count+1:
                    raise ValueError('Clock entry gap/nesting')
                clock = number
            else:
                if clock is None or number!=clock:
                    raise ValueError('Clock exit unmatched')
                clock_count += 1
                clock = None
            actors = rows[index+1:index+3]
            if len(actors)!=2 or any(r['kind']!='actor-state' for r in actors) or [unquote(r['data'].split(',')[0]) for r in actors]!=['p1','p2']:
                raise ValueError('Clock boundary actor pair missing')
            for actor in actors:
                values = actor['data'].split(',')
                if len(values)!=10 or any(not re.fullmatch(r'f:-?1:-?\d+:\d+:\d+', unquote(v)) for v in values[1:]):
                    raise ValueError('Incomplete actor state at clock boundary')
    if clock is not None:
        raise ValueError('Clock callback truncated')
    if not callbacks or not clock_count or not any(k['data'].split(',')[2]=='true' for k in keys):
        raise ValueError('Active-fight positive query or paired timer observations absent')
    return dict(active_fight_queries=len(keys), timer_pairs=clock_count,
                certified_global_tick=False, exact_initial_state=False)


def analyze(directory, build_path):
    build = json.loads(build_path.read_text())
    if build.get('facility')!='r05':
        raise ValueError('Requires r05 build provenance')
    for name,digest in build['facility_sha256'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Facility source hash mismatch')
    if directory is None:
        raise ValueError('No r05 live capture; offline build cannot prove observations')
    session = json.loads((directory/'session.json').read_text())
    if session['observer_build']!=build:
        raise ValueError('Session/build identity mismatch')
    prefix = ('M002|'+build['run_id']+'|').encode()
    before=(directory/'flashlog.prelaunch.log').read_bytes()
    baseline=(directory/'flashlog.input-baseline.log').read_bytes()
    final=(directory/'flashlog.after.log').read_bytes()
    raw=(directory/'tagged.log').read_bytes()
    if prefix in before or not final.startswith(baseline):
        raise ValueError('Tag reuse or nonappend interval')
    if any(l.startswith(b'M002|') and not l.startswith(prefix) for l in final.splitlines()):
        raise ValueError('Foreign observer tag shares retained final log')
    if b'\n'.join(l for l in final.splitlines() if l.startswith(prefix))+b'\n' != raw:
        raise ValueError('Raw/tagged selection mismatch')
    if not session.get('input_operations') or session.get('remaining_movie_pids')!=[] or session.get('asset_recheck')!='passed':
        raise ValueError('Input/cleanup/asset receipt incomplete')
    for op in session['input_operations']:
        if op['pid']!=session['movie_pid'] or not op.get('result','').startswith(str(session['movie_pid'])+', true,'):
            raise ValueError('Movie input PID mismatch')
    return validate_rows(raw,build)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=HERE/'build.json')
    parser.add_argument('--directory',type=Path)
    parser.add_argument('--require-oracle',action='store_true')
    args=parser.parse_args()
    report=dict(production_admitted=False,native_parity_proven=False,oracle_accepted=False)
    try:
        report.update(analyze(args.directory,args.build))
        report['refusal']='Certified initial boundary/global tick, full random tape, deterministic repeat and noninterference remain unproved'
    except (ValueError,KeyError,OSError,UnicodeError) as error:
        report['refusal']=str(error)
    print(json.dumps(report,indent=2))
    return 1


if __name__=='__main__':
    raise SystemExit(main())
