"""Report live marker observations; preserve the unchanged r05 structural refusal."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def startfight_windows(markers,validate):
    windows=[]
    active=None
    for row in markers:
        if row['kind']=='startfight-entry':
            if active is not None:raise ValueError('Nested startFight interval')
            active=[]
        if active is not None:active.append(row)
        if row['kind']=='startfight-exit':
            if active is None:raise ValueError('Unmatched startFight exit')
            result=validate(active)
            windows.append(dict(events=active,shape=result))
            active=None
    if active is not None:raise ValueError('Unterminated startFight interval')
    if not windows:raise ValueError('No source startFight interval')
    return windows


def analyze(directory):
    old=load('r05_analysis',HERE.parent/'native-fight-r05/analyze.py')
    builder=load('r03_build',HERE.parent/'native-fight-r03/build_observer.py')
    session=json.loads((directory/'session.json').read_text())
    build=json.loads((HERE/'build.json').read_text())
    if session['observer_build']!=build or build['facility']!='r14':raise ValueError('Build/session mismatch')
    prefix=('M002|'+build['run_id']+'|').encode()
    pre=(directory/'flashlog.prelaunch.log').read_bytes()
    baseline=(directory/'flashlog.input-baseline.log').read_bytes()
    final=(directory/'flashlog.after.log').read_bytes()
    raw=(directory/'tagged.log').read_bytes()
    if prefix in pre or not final.startswith(baseline):raise ValueError('Freshness/append mismatch')
    if any(l.startswith(b'M002|') and not l.startswith(prefix) for l in final.splitlines()):raise ValueError('Foreign observer tag')
    if b'\n'.join(l for l in final.splitlines() if l.startswith(prefix))+b'\n'!=raw:raise ValueError('Raw/tag selection mismatch')
    if session.get('remaining_movie_pids')!=[] or session.get('asset_recheck')!='passed':raise ValueError('Cleanup/assets incomplete')
    if not session['input_operations']:raise ValueError('No physical input receipt')
    for op in session['input_operations']:
        if op['pid']!=session['movie_pid'] or not op.get('result','').startswith(str(session['movie_pid'])+', true,'):raise ValueError('Input binding mismatch')
    # Recheck retained copies; loss of a temporary copy must not silently pass.
    copy=Path(session['build']['path'])
    for name,digest in build['outputs_sha256'].items():
        if builder.sha(copy/name)!=digest:raise ValueError('Copy hash mismatch')
    for name,expected in build['changed_tag_paths_by_asset'].items():
        a,b=builder.tags(ROOT/name),builder.tags(copy/name)
        if a.keys()!=b.keys() or [k for k in a if a[k]!=b[k]]!=expected:raise ValueError('Tag audit mismatch')
    rows=old.base.parse(raw,build['run_id'])
    markers=[r for r in rows if r['kind'] in ['loader-request','load-complete-entry','load-complete-exit','decision-installed','chushi-hp-before','chushi-hp-after']]
    snapshots=[]
    incomplete=[]
    for i,row in enumerate(rows):
        if row['kind'].startswith('chushi-hp-'):
            snapshots.append(dict(marker=row,actors=rows[i+1:i+3]))
        if row['kind'] in ('clock-entry','clock-exit'):
            actors=rows[i+1:i+3]
            if any('undefined' in a['data'] for a in actors):incomplete.append(dict(marker=row,actors=actors))
    keys=[r for r in rows if r['kind']=='fight-key-return']
    positive=[r for r in keys if r['data'].split(',')[2]=='true']
    report=dict(production_admitted=False,native_parity_proven=False,oracle_accepted=False,
                run_tag=build['run_id'],movie_pid=session['movie_pid'],duration_seconds=session['completed_unix']-session['started_unix'],
                counts=dict(Counter(r['kind'] for r in rows)),events=len(rows),fresh_exclusive_tag_selection=True,
                fight_key_total=len(keys),fight_key_positive=len(positive),positive_sites=dict(Counter(r['data'].split(',')[0] for r in positive)),
                first_positive_queries=positive[:20],markers=markers,hp_boundaries=snapshots,incomplete_clock_boundaries=incomplete,
                all_copy_hashes_and_tags_match=True,structural_observations_admitted=False,
                limits=['observations are not certified input consumption ticks','local clocks are not global ticks','onLoadComplete is not onLoadInit','no full RNG tape/repeat/noninterference proof'])
    try:
        report['r05_structural_result']=old.validate_rows(raw,build)
        report['structural_observations_admitted']=True
    except ValueError as exc:
        report['structural_refusal']=str(exc)
    marker_gate=load('r12_shape',HERE.parent/'native-fight-r12/analyze.py')
    start_markers=[r for r in rows if r['kind'] in marker_gate.KINDS]
    report['startfight_menu_markers']=start_markers
    report['startfight_menu_decoded']=[dict(seq=r['seq'],kind=r['kind'],fields=list(map(unquote,r['data'].split(',')))) for r in start_markers]
    try:
        report['startfight_windows']=startfight_windows(start_markers,marker_gate.validate_boundary)
    except ValueError as exc:
        report['startfight_marker_refusal']=str(exc)
        report['startfight_windows']=[]
    report['startfight_actor_snapshots']=[dict(marker=r,actors=rows[i+1:i+3]) for i,r in enumerate(rows) if r['kind'] in ('startfight-entry','startfight-exit')]
    consumer=load('r15_consumer',HERE/'consumer_join.py')
    report['consumer_analysis']=consumer.join(rows)
    report['certified_global_tick']=False
    report['os_input_join_proven']=False
    (HERE/'observations.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=HERE/'run-01');p.add_argument('--require-oracle',action='store_true');a=p.parse_args()
    try:
        r=analyze(a.directory)
        print(json.dumps({k:r[k] for k in ['events','fight_key_total','fight_key_positive','positive_sites','structural_observations_admitted']}))
        print(r.get('structural_refusal','Full oracle obligations remain unproved'))
    except (ValueError,KeyError,OSError) as exc:print('Refused: '+str(exc))
    raise SystemExit(1)
