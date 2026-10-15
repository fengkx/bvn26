"""Execute fresh-fight move fixtures; execution alone is not original parity."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

if __package__:
    from .godot_result import process_succeeded
else:
    from godot_result import process_succeeded

ROOT = Path(__file__).resolve().parents[1]


def validate_timer_contract(case):
    """Fail closed when source build metadata requires an external timer clock."""
    source_build = case.get('source_build')
    if not source_build:
        return
    metadata_path = Path(source_build).expanduser()
    if not metadata_path.is_absolute():
        metadata_path = (ROOT / metadata_path).resolve()
    else:
        metadata_path = metadata_path.resolve()
    if not metadata_path.exists():
        raise ValueError(f'source_build does not exist: {metadata_path}')
    metadata = json.loads(metadata_path.read_text())
    configuration = metadata.get('configuration', metadata)
    dynamic_case = metadata.get('move_case', {})
    if not isinstance(dynamic_case, dict):
        dynamic_case = {}
    required = bool(configuration.get('drive_source_timers',
                                      dynamic_case.get('drive_source_timers',
                                                       metadata.get('drive_source_timers', False))))
    if required and not case.get('source_timer_required', False):
        raise ValueError(f'source build requires timer input but fixture omits source_timer_required: {case.get("id")}')
    if required and not case.get('drive_source_timers', False):
        raise ValueError(f'source build requires timer input but fixture disables it: {case.get("id")}')
    if case.get('drive_source_timers') and not case.get('timer_input_provenance', {}).get('route'):
        raise ValueError(f'timer-driven fixture lacks timer_input_provenance.route: {case.get("id")}')


def resolve_cli_paths(godot, cases, output):
    return tuple(path.expanduser().resolve() for path in (godot, cases, output))


def target_frame_ranges(case):
    values = case.get('target_frames', [])
    if not isinstance(values, list) or len(values) % 2:
        raise ValueError('target_frames must contain start/end pairs')
    ranges = []
    for start, end in zip(values[::2], values[1::2]):
        if start is None and end is None:
            continue
        if not isinstance(start, int) or not isinstance(end, int) or start > end:
            raise ValueError('target_frames contains an invalid range')
        ranges.append((start, end))
    return ranges


def target_seen(case, rows):
    ranges = target_frame_ranges(case)
    return any(row['slot'] == case['slot'] and start <= row['frame'] <= end
               for row in rows for start, end in ranges)


def execute(godot, case_path, output):
    case=json.loads(case_path.read_text())
    validate_timer_contract(case)
    target=output/(case_path.stem+'.json')
    command=[str(godot),'--headless','--path',str(ROOT/'godot'),
             '--log-file',str(output/(case_path.stem+'.engine.log')),
             '-s','res://tests/move_case_reference.gd','--quit-after','1200','--',str(case_path),str(target)]
    try:
        run=subprocess.run(command,capture_output=True,text=True,timeout=45)
    except subprocess.TimeoutExpired:
        return {'id':case['id'],'executed':False,'status':'timeout'}
    log=run.stdout+run.stderr
    (output/(case_path.stem+'.log')).write_text(log)
    rows=json.loads(target.read_text()) if target.exists() else []
    complete=len(rows)==2*(case['frames']+1)
    executed = process_succeeded(run.returncode, log, required_marker='MOVE_CASE_REFERENCE_OK') and complete
    seen = target_seen(case, rows)
    return {'id':case['id'],'executed':executed,'states':len(rows),'target_seen':seen,
            'status':'native_only_not_parity' if executed else 'failed'}



def execute_batch(godot, paths, output):
    index = output / 'case-paths.json'
    index.write_text(json.dumps([str(p) for p in paths]))
    cases = [json.loads(path.read_text()) for path in paths]
    # Validate every source contract before starting Godot. A malformed case
    # must never produce a partial native trace that looks like evidence.
    for case in cases:
        validate_timer_contract(case)
    command = [str(godot), '--headless', '--path', str(ROOT / 'godot'),
               '--log-file', str(output / 'engine.log'), '-s', 'res://tests/move_case_reference.gd',
               '--quit-after', str(max(2400, len(paths) * 60)), '--', '--batch', str(index), str(output)]
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=60 + len(paths) * 10)
        log = run.stdout + run.stderr
        clean = process_succeeded(run.returncode, log, required_marker='MOVE_CASE_BATCH_OK')
    except subprocess.TimeoutExpired as error:
        log = str(error)
        clean = False
    (output / 'batch.log').write_text(log)
    results = []
    for path, case in zip(paths, cases):
        target = output / (case['id'] + '.json')
        rows = json.loads(target.read_text()) if target.exists() else []
        complete = len(rows) == 2 * (case['frames'] + 1)
        seen = target_seen(case, rows)
        executed = clean and complete and ('MOVE_CASE_REFERENCE_OK ' + case['id']) in log
        results.append({'id': case['id'], 'executed': executed, 'states': len(rows),
                        'target_seen': seen, 'status': 'native_only_not_parity' if executed else 'failed'})
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot',type=Path,required=True)
    parser.add_argument('--cases',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--jobs',type=int,default=1)
    args=parser.parse_args()
    # Godot resolves command-line file arguments relative to the project, and
    # --log-file may be treated as user://. Anchor every external path at the
    # caller's working directory before handing it to the engine.
    args.godot, args.cases, args.output = resolve_cli_paths(args.godot, args.cases, args.output)
    if args.output.exists(): raise ValueError('Use a fresh output directory')
    args.output.mkdir(parents=True)
    paths = sorted(args.cases.glob('*.json'))
    if args.jobs == 1:
        results = execute_batch(args.godot, paths, args.output)
    else:
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(lambda p: execute(args.godot, p, args.output), paths))
    (args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'cases':len(results),'executed':sum(r['executed'] for r in results),'status':'native_only_not_parity'}))
    raise SystemExit(0 if all(r['executed'] for r in results) else 1)


if __name__=='__main__': main()
