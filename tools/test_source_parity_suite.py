"""Replay a retained Flash fixture archive and compare all 14 fighter fields."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/probes'))
from compare_mode_reference import compare, validate_probe_provenance
from test_move_cases import validate_timer_contract
from godot_result import process_succeeded


def unpack(suite, output):
    locked = json.loads((ROOT / 'manifest.json').read_text())['file_sha256']
    with tarfile.open(suite) as archive:
        index = json.load(archive.extractfile('suite.json'))
        assert index['format'] == 'bvn-source-parity-suite-v1'
        seen = set()
        for record in index['cases']:
            name = record['id']
            assert re.fullmatch(r'[A-Za-z0-9_-]+', name) and name not in seen
            seen.add(name)
            for relative, field in [(f'cases/{name}.json', 'fixture_sha256'),
                                    (f'original/{name}/events.jsonl', 'events_sha256'),
                                    (f'original/{name}/build.json', 'build_sha256')]:
                data = archive.extractfile(relative).read()
                assert hashlib.sha256(data).hexdigest() == record[field], relative
                path = output / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            build = json.loads((output / 'original' / name / 'build.json').read_text())
            provenance = validate_probe_provenance(output / 'original' / name / 'events.jsonl')
            assert provenance['status'] == 'verified', name
            for relative, expected in build['sources_sha256'].items():
                assert locked[relative] == expected, relative
                assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
            case = json.loads((output / 'cases' / (name + '.json')).read_text())
            for field in ('inputs', 'setup', 'frames', 'fighters',
                          'source_state_preconditions', 'resource_interventions'):
                assert case.get(field) == build['move_case'].get(field), (name, field)
            validate_timer_contract(case)
            assert case['id'] == name
            if 'recorded_nextfight' in case:
                assert case['timer_input_provenance']['source_trace_sha256'] == record['events_sha256']
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--godot', type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--native', type=Path, action='append',
                        help='Compare existing native traces instead of executing Godot')
    args = parser.parse_args()
    if not args.native and not args.godot:
        parser.error('--godot is required unless --native supplies existing traces')
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    index = unpack(args.suite, output)
    execution = []
    native_dirs = [p.resolve() for p in args.native] if args.native else [output / 'native']
    if not args.native:
        native_dirs[0].mkdir()
        paths = sorted((output / 'cases').glob('*.json'))
        batches = [paths[i::args.jobs] for i in range(min(args.jobs, len(paths)))]

        def execute(item):
            number, batch = item
            batch_index = output / f'batch-{number}.json'
            batch_index.write_text(json.dumps([str(path) for path in batch]))
            command = [str(args.godot.resolve()), '--headless', '--path', str(ROOT / 'godot'),
                       '--log-file', str(output / f'engine-{number}.log'),
                       '-s', 'res://tests/move_case_timer_reference.gd', '--quit-after', '10000',
                       '--', '--batch', str(batch_index), str(native_dirs[0])]
            run = subprocess.run(command, capture_output=True, text=True, timeout=3600)
            log = run.stdout + run.stderr
            (output / f'batch-{number}.log').write_text(log)
            return {'batch': number, 'cases': len(batch),
                    'passed': process_succeeded(run.returncode, log, required_marker='MOVE_CASE_BATCH_OK')}

        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            execution = list(pool.map(execute, enumerate(batches)))
    results = []
    for record in index['cases']:
        name = record['id']
        matches = [directory / (name + '.json') for directory in native_dirs
                   if (directory / (name + '.json')).exists()]
        assert len(matches) == 1, f'Expected exactly one native trace: {name}'
        result = compare(output / 'original' / name / 'events.jsonl', matches[0])
        results.append({'id': name, 'group': record['group'],
                        'previous_status': record.get('previous_status'),
                        'source_trace_sha256': record['events_sha256'],
                        'native_trace_sha256': hashlib.sha256(matches[0].read_bytes()).hexdigest(),
                        **result})
    passed = all(r['status'] == 'matched' for r in results) and all(r['passed'] for r in execution)
    report = {'status': 'passed' if passed else 'failed', 'cases': len(results),
              'matched': sum(r['status'] == 'matched' for r in results),
              'source_states': sum(r['source_states'] for r in results),
              'execution': execution, 'used_existing_traces': bool(args.native), 'results': results}
    (output / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('status', 'cases', 'matched', 'source_states')}))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
