import gzip, hashlib, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path[:0] = ['tools', 'tools/probes']
from test_move_cases import validate_timer_contract, target_seen
from compare_mode_reference import compare
root = Path.cwd()
out = Path(os.environ['BVN_CHECK_DIR']) / 'flash-replay'
out.mkdir()
godot = Path(os.environ['BVN_GODOT'])
index = json.loads(Path('evidence/characters/itachi/review-mediums/regressions.json').read_text())
assert index['cases'] == len(index['results']) == 103
assert len(index['fighters']) == 16
for fighter in ['orochimaru', 'jiraiya', 'pain', 'konan', 'daitu', 'didala', 'lanran']:
    for row in json.loads(Path(f'evidence/characters/{fighter}/comparisons.json').read_text()):
        index['results'].append({'id': row['id'], 'fixture': row['paths']['fixture'],
                                 'source': row['paths']['source'], 'hashes': row['hashes']})

for case in index['results']:
    assert hashlib.sha256(Path(case['fixture']).read_bytes()).hexdigest() == case['hashes']['fixture']
    assert hashlib.sha256(gzip.decompress(Path(case['source']).read_bytes())).hexdigest() == case['hashes']['source']
def replay(case):
    folder = out / case['id']
    folder.mkdir()
    fixture = (root / case['fixture']).resolve()
    started = time.monotonic()
    case_data = json.loads(fixture.read_text())
    validate_timer_contract(case_data)
    native = folder / (fixture.stem + '.json')
    command = [str(godot), '--headless', '--path', str(root / 'godot'),
               '--log-file', str(folder / 'engine.log'),
               '-s', 'res://tests/move_case_reference.gd', '--quit-after', '1200',
               '--', str(fixture), str(native)]
    timed_out = False
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=600)
        log, code = run.stdout + run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        def text(value):
            return value.decode(errors='replace') if isinstance(value, bytes) else (value or '')
        log, code, timed_out = text(exc.stdout) + text(exc.stderr), -1, True
    (folder / 'process.log').write_text(log)
    rows = json.loads(native.read_text()) if native.exists() and not timed_out else []
    complete = len(rows) == 2 * (case_data['frames'] + 1)
    executed = code == 0 and 'MOVE_CASE_REFERENCE_OK' in log and 'SCRIPT ERROR' not in log and complete
    execution = {'executed': executed, 'exit': code, 'timed_out': timed_out,
                 'states': len(rows), 'target_seen': target_seen(case_data, rows)}
    comparison = compare(root / case['source'], native) if execution['executed'] else None
    print(case['id'], comparison['status'] if comparison else execution, flush=True)
    return {'id': case['id'], 'execution': execution, 'comparison': comparison,
            'seconds': time.monotonic() - started}
started = time.monotonic()
with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(replay, index['results']))
report = {'seconds': time.monotonic() - started, 'results': results}
(out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
assert all(r['execution']['executed'] and r['comparison']['status'] == 'matched' for r in results)
assert sum(r['comparison']['source_states'] for r in results) == 102518
print('FLASH_REPLAY_OK cases=179 primary_fighters=22 states=102518', report['seconds'])
