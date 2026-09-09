"""Compare observed Ready-boundary frames without claiming full battle replay."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', required=True, type=Path)
    parser.add_argument('--reference', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    build = json.loads((args.reference / 'build.json').read_text())
    required = {'modo': 2, 'p1': '鸣人', 'p2': '一护', 'AI': 5, 'stage': '现世',
                'p2cpu': True, 'p1sf': '我爱罗', 'p2sf': '魂'}
    if any(build['configuration'].get(key) != value for key, value in required.items()):
        raise ValueError('Reference does not match the fixed native configuration')
    for name, digest in build['sources_sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Reference source hash mismatch: ' + name)
    path = args.reference / 'events.jsonl'
    events = [json.loads(line) for line in path.read_text().splitlines()]
    ready = [event for event in events if event['kind'] == 'ready']
    if len(ready) != 1:
        raise ValueError('Expected exactly one original Ready event')
    boundary = ready[0]
    for event in events:
        if event['sequence'] >= boundary['sequence']:
            break
        if event['kind'] == 'input_next_display' and any(
                value.split('=', 1)[1] != 'undefined' for value in event['value'].split(',')):
            raise ValueError('Pre-Ready input requires an input replay')
    if any(event['kind'] == 'predicate' and event['sequence'] < boundary['sequence'] for event in events):
        raise ValueError('Pre-Ready predicates require random/timer replay')
    expected = []
    for event in events:
        if event['kind'] != 'state' or event['fight_tick'] != 0:
            continue
        parts = event['value'].split(',')
        expected.append({'slot': parts[0], 'frame': int(parts[1]),
                         'x': float(parts[2]), 'y': float(parts[3]),
                         'hp': float(parts[6]), 'ql': float(parts[7]),
                         'source_action': int(parts[5]), 'paused': parts[12] == 'true'})
    if [state['slot'] for state in expected] != ['p1', 'p2']:
        raise ValueError('Missing or repeated boundary fighter states')
    with tempfile.TemporaryDirectory(prefix='bvn-ready-') as work:
        command = [str(args.godot.resolve()), '--headless', '--path', str(ROOT / 'godot'),
                   '--log-file', str(Path(work) / 'godot.log'), '--script',
                   'res://tests/ai_ready_reference.gd']
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=60)
        prefix = 'AI_READY_CAPTURE '
        captures = [json.loads(line[len(prefix):]) for line in result.stdout.splitlines()
                    if line.startswith(prefix)]
        if result.returncode or 'SCRIPT ERROR' in result.stdout or len(captures) != 1:
            raise RuntimeError('Native Ready capture failed:\n' + result.stdout)
    actual = captures[0]
    differences = []
    for phase in ('before_tick', 'signal', 'after_tick'):
        if [state['slot'] for state in actual[phase]] != ['p1', 'p2']:
            raise ValueError('Unexpected native slots')
        for original, native in zip(expected, actual[phase]):
            for field in ('frame', 'x', 'y', 'hp', 'ql', 'source_action', 'paused'):
                if original[field] != native[field]:
                    differences.append({'phase': phase, 'slot': original['slot'], 'field': field,
                                        'original': original[field], 'native': native[field]})
    report = {
        'status': 'boundary_difference_detected' if differences else 'boundary_fields_match',
        'original_parity_verified': False,
        'reference_run': boundary['run_id'],
        'reference_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'original_ready': boundary, 'original_states': expected, 'native': actual,
        'differences': differences,
        'limits': [
            'This is not a full input/random/timer replay; native AI random clock is cancelled.',
            'No pre-Ready predicates were recorded in this reference, but other timer effects remain unchecked.',
            'Original snapshot runs in the root enterFrame; native signal/tick phases are reported separately.',
            'No frame shift or numeric tolerance is applied; x differences include float representation.',
            'A phase discrepancy requires source scheduling analysis, not forced playhead alignment.',
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    args.output.with_suffix('.log').write_text(result.stdout)
    print(json.dumps({'status': report['status'], 'differences': len(differences)}))


if __name__ == '__main__':
    main()
