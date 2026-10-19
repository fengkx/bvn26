"""Replay the 40-case audit, allowing only the two authorized Flash deviations."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).parent / 'probes'))
from compare_mode_reference import compare, source_rows

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / 'evidence/characters/_audit-sample-2026-10-19'
DEVIATIONS = {'orochimaru-prep-counter-super', 'pain-prep-counter-super'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def recovery(rows, slot):
    actors = {key: [row for row in rows if row['slot'] == key] for key in ('p1', 'p2')}
    assert all([row['tick'] for row in values] == list(range(241)) for values in actors.values())
    victim = actors[slot]
    opponent = actors['p2' if slot == 'p1' else 'p1']
    assert victim[15]['hp'] == 1000 and victim[15]['ql'] == 300
    assert victim[16]['action'] == 3 and victim[16]['ql'] == 200
    assert victim[17]['hp'] == 960
    assert any(row['action'] == 3 and row['paused'] for row in opponent[20:40])
    assert all(not row['paused'] for row in rows if row['tick'] >= 100)
    assert all(values[-1]['action'] == 0 for values in actors.values())
    assert victim[-1]['hp'] < 960, 'Counter super must continue into its actual hit'
    assert all(len({row['frame'] for row in values[200:]}) > 1 for values in actors.values())
    return {'last_paused_tick': max(row['tick'] for row in rows if row['paused']),
            'final': rows[-2:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    cases = json.loads((AUDIT / 'comparisons.json').read_text())
    assert len(cases) == 40
    jobs = []
    for case in cases:
        fixture = ROOT / case['fixture']
        source = AUDIT / 'traces' / (case['id'] + '.original.jsonl.gz')
        assert digest(fixture.read_bytes()) == case['hashes']['fixture']
        assert digest(gzip.decompress(source.read_bytes())) == case['hashes']['original_events']
        jobs.append((fixture, source, case['id'] in DEVIATIONS))
        if case['id'] not in DEVIATIONS:
            continue
        original = json.loads(fixture.read_text())
        for variant in ('swap-slots', 'counter-one-tick-later'):
            data = json.loads(json.dumps(original))
            data['id'] += '-' + variant
            if variant == 'swap-slots':
                data['slot'] = 'p2'
                for key in ('fighters', 'setup'):
                    data[key] = {'p1': data[key]['p2'], 'p2': data[key]['p1']}
                for event in data['inputs']:
                    event['slot'] = 'p2' if event['slot'] == 'p1' else 'p1'
            else:
                for event in data['inputs']:
                    if event['slot'] == 'p2' and event['keys'] == ['special']:
                        event['start'] += 1
                        event['end'] += 1
            path = out / (data['id'] + '.fixture.json')
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
            jobs.append((path, None, True))

    def replay(job):
        fixture, source, deviation = job
        data = json.loads(fixture.read_text())
        name = data['id']
        native = out / (name + '.json')
        command = [args.godot, '--headless', '--path', str(ROOT / 'godot'),
                   '--log-file', str(out / (name + '.engine.log')),
                   '-s', 'res://tests/move_case_reference.gd', '--', str(fixture), str(native)]
        before = time.monotonic()
        run = subprocess.run(command, capture_output=True, text=True, timeout=600)
        log = run.stdout + run.stderr
        (out / (name + '.log')).write_text(log)
        assert run.returncode == 0 and 'SCRIPT ERROR' not in log and 'Parse Error' not in log, name
        assert 'MOVE_CASE_REFERENCE_OK ' + name in log, name
        rows = json.loads(native.read_text())
        result = {'id': name, 'elapsed_seconds': round(time.monotonic() - before, 3),
                  'fixture_sha256': digest(fixture.read_bytes()),
                  'native_sha256': digest(native.read_bytes()), 'states': len(rows),
                  'expectation': 'intentional_flash_deviation_recovery' if deviation else 'exact_parity'}
        if source:
            comparison = compare(source, native)
            result['comparison'] = comparison
            result['original_sha256'] = digest(gzip.decompress(source.read_bytes()))
            assert comparison['complete'] and comparison['source_states'] == 482, name
            if deviation:
                original = source_rows(source)
                assert all(row['paused'] for row in original if row['tick'] >= 25)
                assert comparison['differences'][0]['tick'] == 38, name
                assert all(diff['fields'] == {'paused': {'original': True, 'native': False}}
                           for diff in comparison['differences'] if diff['tick'] == 38), name
            else:
                assert comparison['status'] == 'matched', name
        if deviation:
            result['recovery'] = recovery(rows, data['slot'])
        (out / (name + '.json.gz')).write_bytes(gzip.compress(native.read_bytes(), mtime=0))
        print(name + ': PASS ' + result['expectation'], flush=True)
        return result

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(replay, jobs))
    report = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'godot_version': subprocess.check_output([args.godot, '--version'], text=True).strip(),
              'runtime_sha256': digest((ROOT / 'godot/fighter_runtime.gd').read_bytes()),
              'elapsed_seconds': round(time.monotonic() - started, 3),
              'exact_parity': 38, 'intentional_deviations': 2, 'additional_recovery_sequences': 4,
              'results': results}
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('PREP_COUNTER_SUPER_OK parity=38 deviations=2 additional=4')


if __name__ == '__main__':
    main()
