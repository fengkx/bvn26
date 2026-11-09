"""Describe retained observations without replacing the r05 acceptance gate."""
import collections
import importlib.util
import json
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize():
    parser=load('r03_parse', HERE.parent/'native-fight-r03/analyze.py')
    builder=load('r03_build', HERE.parent/'native-fight-r03/build_observer.py')
    run=HERE/'run-01'
    session=json.loads((run/'session.json').read_text())
    build=json.loads((HERE/'build.json').read_text())
    if session['observer_build']!=build:
        raise ValueError('Build/session mismatch')
    prefix=('M002|'+build['run_id']+'|').encode()
    final=(run/'flashlog.after.log').read_bytes()
    tagged=(run/'tagged.log').read_bytes()
    if prefix in (run/'flashlog.prelaunch.log').read_bytes() or not final.startswith((run/'flashlog.input-baseline.log').read_bytes()):
        raise ValueError('Freshness/append mismatch')
    if b'\n'.join(line for line in final.splitlines() if line.startswith(prefix))+b'\n'!=tagged:
        raise ValueError('Raw/tag selection mismatch')
    rows=parser.parse(tagged,build['run_id'])
    movie_copy=Path(session['build']['path'])
    for name,digest in build['outputs_sha256'].items():
        if builder.sha(movie_copy/name)!=digest:
            raise ValueError('Retained movie copy mismatch')
    tag_changes={}
    for name,expected in build['changed_tag_paths_by_asset'].items():
        before,after=builder.tags(ROOT/name),builder.tags(movie_copy/name)
        actual=[key for key in before if before[key]!=after[key]]
        if before.keys()!=after.keys() or actual!=expected:
            raise ValueError('Tag audit mismatch')
        tag_changes[name]=actual
    clocks=[row for row in rows if row['kind'].startswith('clock-')]
    if [(r['kind'], int(r['data'].split(',')[0])) for r in clocks] != [(kind, n) for n in range(1,25) for kind in ('clock-entry','clock-exit')]:
        raise ValueError('Observed clock boundary sequence mismatch')
    incomplete=[]
    for index,row in enumerate(rows):
        if row['kind'].startswith('clock-'):
            actors=rows[index+1:index+3]
            if any('undefined' in actor['data'] for actor in actors):
                incomplete.append(dict(boundary=row,actors=actors))
    keys=[r for r in rows if r['kind']=='fight-key-return']
    probes={p.name:json.loads(p.read_text())['frontmost_pid'] for p in sorted(run.glob('*-before.json'))+sorted(run.glob('*-after.json'))}
    report=dict(kind='descriptive-observations-not-admission',production_admitted=False,native_parity_proven=False,oracle_accepted=False,
                duration_seconds=session['completed_unix']-session['started_unix'],movie_pid=session['movie_pid'],run_tag=build['run_id'],
                events=len(rows),counts=dict(collections.Counter(r['kind'] for r in rows)),
                fight_key_events=len(keys),positive_fight_key_events=sum(r['data'].split(',')[2]=='true' for r in keys),
                clock_entries=sum(r['kind']=='clock-entry' for r in clocks),clock_exits=sum(r['kind']=='clock-exit' for r in clocks),
                first_clock=clocks[0],last_clock=clocks[-1],incomplete_clock_boundaries=len(incomplete),first_incomplete_clock=incomplete[0] if incomplete else None,
                sampled_frontmost=probes,cleanup=session['remaining_movie_pids'],asset_recheck=session['asset_recheck'],
                changed_tag_paths_by_asset=tag_changes,all_75_retained_copy_hashes_match=True,
                limitation='Descriptive counts do not admit incomplete prefix; local callback clocks are not global ticks; no fight-key event is not proof that physical J was not consumed.')
    (HERE/'observations.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['events','counts','incomplete_clock_boundaries','fight_key_events']}))


if __name__=='__main__':summarize()
