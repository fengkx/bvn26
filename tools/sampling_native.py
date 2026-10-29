"""Case-bound native capture receipts; capture completeness is not parity."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from tools.probes import capture_native_player as player
from tools.probes.collect_ai_reference import decode_number

ROOT = Path(__file__).resolve().parents[1]
PROBES = [ROOT / 'tools/probes/build_ai_reference.py',
          ROOT / 'tools/probes/move_cases.py', ROOT / 'tools/probes/chad_lifecycle_observer.py', ROOT / 'tools/probes/doaction_observer.py', ROOT / 'tools/probes/callsite_observer.py', ROOT / 'tools/probes/capture_native_player.py',
          ROOT / 'tools/probes/collect_ai_reference.py', Path(__file__).resolve(),
          ROOT / 'evidence/reference-environment.md']
PROBES += sorted((ROOT / 'tools/probes/as2/ai_reference').glob('*.as'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_capture(case, metadata, trace):
    if metadata['move_case'] != case:
        raise ValueError('native evidence: changed input tape or case identity')
    if metadata.get('dynamic_move_case'):
        raise ValueError('native evidence: dynamic fixture loading is not admitted by this adapter')
    if metadata['frames_after_ready'] != case['frames']:
        raise ValueError('native evidence: wrong capture duration')
    config = metadata['configuration']
    catalog = json.loads((ROOT / 'manifest.json').read_text())['fighter_catalog']
    for slot, fighter in case['fighters'].items():
        if Path(catalog[config[slot]]['url']).stem.lower() != fighter.lower():
            raise ValueError('native evidence: wrong fighter configuration')
    if (config['modo'] != 3 or config['p2cpu'] is not False or config['stage'] != case['stage']
            or config['p1sf'] != case['p1_helper'] or config['p2sf'] != case['p2_helper']):
        raise ValueError('native evidence: wrong match configuration')
    rows = []
    done = []
    sequence = []
    terminal = None
    expected = [(tick, slot) for tick in range(case['frames'] + 1) for slot in ('p1', 'p2')]
    for line in trace.read_text().splitlines():
        parts = line.split('|', 7)
        if len(parts) != 8 or parts[:2] != ['AIREF', metadata['run_id']]:
            raise ValueError('native evidence: malformed or foreign run event')
        seq, tick = int(parts[2]), int(parts[5])
        sequence.append(seq)
        display = int(parts[4])
        if terminal is not None and (tick, display) != terminal:
            raise ValueError('native evidence: events beyond completion boundary')
        if parts[6] == 'timeout':
            raise ValueError('native evidence: capture timed out')
        if parts[6] == 'state' and tick >= 0:
            fields = parts[7].split(',')
            if len(fields) != 15 or any(not field for field in fields):
                raise ValueError('native evidence: incomplete state payload')
            if any(not math.isfinite(decode_number(fields[i])) for i in (1, 2, 3, 4, 6, 7)):
                raise ValueError('native evidence: nonfinite state')
            if tick == 10 and fields[0] == 'p1':
                expected_touch = 'true' if case['sampling_cell']['posture'] == 'ground' else 'false'
                if fields[9] != expected_touch:
                    raise ValueError('native evidence: requested posture not reached')
            rows.append((tick, fields[0]))
        if parts[6] == 'done':
            if rows != expected:
                raise ValueError('native evidence: premature completion before final states')
            done.append((tick, seq))
            terminal = (tick, display)
    # quit is requested inside the root observer; native callbacks can still emit
    # events in that same display frame. Retain and hash the entire suffix.

    if sequence != list(range(1, len(sequence) + 1)) or rows != expected:
        raise ValueError('native evidence: missing/duplicate/out-of-order observations')
    if len(done) != 1 or done[0][0] != case['frames']:
        raise ValueError('native evidence: missing or premature completion')


def inspect(case_path, build, trace, engine):
    case = json.loads(case_path.read_text())
    metadata = json.loads((build / 'build.json').read_text())
    validate_capture(case, metadata, trace)
    sources = metadata['sources_sha256']
    outputs = metadata['outputs_sha256']
    required = {'game/main.swf'} | {f'game/fighter/{fighter}.swf' for fighter in case['fighters'].values()}
    # Source filenames can retain authored capitalization (for example Sasuke).
    if not {p.lower() for p in required} <= {p.lower() for p in sources}:
        raise ValueError('native evidence: missing source SWF bindings')
    if 'game/main.swf' not in outputs:
        raise ValueError('native evidence: missing instrumented main SWF')
    files = {case_path.resolve(), (build / 'build.json').resolve(), trace.resolve(), engine.resolve(), *PROBES}
    for hashes, root in ((sources, ROOT), (outputs, build)):
        for name, expected in hashes.items():
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()) or sha(path) != expected:
                raise ValueError(f'native evidence: artifact hash mismatch: {name}')
            files.add(path)
    instrumentation = build / 'instrumentation.diff'
    if sha(instrumentation) != metadata['instrumentation_sha256']:
        raise ValueError('native evidence: instrumentation hash mismatch')
    files.add(instrumentation.resolve())
    return {str(path): sha(path) for path in sorted(files)}


def seal(case, build, trace, engine, receipt):
    files = inspect(case, build, trace, engine)
    data = {'version': 1, 'case_id': json.loads(case.read_text())['id'],
            'case_sha256': sha(case), 'build': str(build.resolve()),
            'trace': str(trace.resolve()), 'engine': str(engine.resolve()), 'files': files,
            'native_parity_proven': False, 'production_admitted': False}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(data, indent=2) + '\n')
    return data


def validate(case, receipt):
    data = json.loads(receipt.read_text())
    if (data['version'] != 1 or data['case_id'] != json.loads(case.read_text())['id']
            or data['case_sha256'] != sha(case)
            or data['native_parity_proven'] is not False or data['production_admitted'] is not False):
        raise ValueError('native evidence: receipt identity mismatch')
    actual = inspect(case, Path(data['build']), Path(data['trace']), Path(data['engine']))
    if data['files'] != actual:
        raise ValueError('native evidence: changed capture/build/engine/probe artifacts')
    return sha(receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--player-app', type=Path, default=player.APP)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--allow-window-activation', action='store_true')
    args = parser.parse_args()
    if not args.allow_window_activation:
        parser.error('capture requires --allow-window-activation')
    try:
        case = json.loads(args.case.read_text())
        metadata = json.loads((args.build / 'build.json').read_text())
        if metadata['move_case'] != case or metadata.get('dynamic_move_case'):
            raise ValueError('native evidence: build must contain this static case tape')
        player.preflight(args.player_app)
        if not player.capture(args.build.resolve(), args.trace.resolve(), args.timeout, args.player_app):
            raise ValueError('native evidence: incomplete capture')
        seal(args.case, args.build, args.trace, player.player_binary(args.player_app), args.receipt)
        print('NATIVE_CAPTURE_RECEIPT_OK native_parity_proven=false')
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
