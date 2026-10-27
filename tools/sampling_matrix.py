"""Generate executable input campaigns; execution coverage is not Flash parity."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

from tools.test_move_cases import execute_batch

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'godot/generated/main/character_selection/available.json'
ACTIONS = ('attack', 'jump', 'dash', 'ranged', 'special', 'summon')
DIRECTIONS = {
    'neutral': [], 'up': ['up'], 'down': ['down'], 'left': ['left'],
    'right': ['right'], 'up_left': ['up', 'left'], 'up_right': ['up', 'right'],
    'down_left': ['down', 'left'], 'down_right': ['down', 'right'],
}
# Experimental setup bins, not claims about authored reach or native outcomes.
DISTANCES = {'near': 50, 'mid': 150, 'far': 300}
STATE_FIELDS = {'tick', 'slot', 'frame', 'x', 'y', 'xscale', 'action', 'hp', 'ql',
                'sw', 'touch', 'touchFloor', 'hits', 'paused', 'hstm', 'hurtSkling'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cells(fighters):
    return [dict(zip(('fighter', 'key', 'direction', 'posture', 'distance'), values))
            for values in itertools.product(sorted(fighters), ACTIONS, DIRECTIONS,
                                            ('ground', 'air'), DISTANCES)]


def fixture(cell, require_native=False):
    case_id = '__'.join(cell.values())
    inputs = []
    if cell['posture'] == 'air':
        inputs.append({'slot': 'p1', 'keys': ['jump'], 'start': 1, 'end': 2})
    inputs.append({'slot': 'p1', 'keys': DIRECTIONS[cell['direction']] + [cell['key']],
                   'start': 10, 'end': 13})
    return {'id': case_id, 'fighter': cell['fighter'], 'slot': 'p1', 'frames': 60,
            'fighters': {'p1': cell['fighter'], 'p2': 'yihu'},
            'p1_helper': '我爱罗', 'p2_helper': '魂', 'stage': '现世',
            'setup': {'p1': {'x': 100, 'energy': 300},
                      'p2': {'x': 100 + DISTANCES[cell['distance']], 'energy': 300}},
            'inputs': inputs, 'target_frames': [], 'sampling_cell': cell,
            **({'require_native': True} if require_native else {})}


def generate(output, fighters=None, require_native=False):
    available = sorted(set(json.loads(CATALOG.read_text())['fighters'].values()))
    fighters = available if fighters is None else sorted(set(fighters))
    if not fighters or set(fighters) - set(available):
        raise ValueError('empty or unknown fighter selection')
    output.mkdir(parents=True, exist_ok=False)
    cases_dir = output / 'cases'
    cases_dir.mkdir()
    entries = []
    for cell in cells(fighters):
        case = fixture(cell, require_native)
        path = cases_dir / (case['id'] + '.json')
        path.write_text(json.dumps(case, ensure_ascii=False, indent=2) + '\n')
        entries.append({'id': case['id'], 'cell': cell, 'sha256': digest(path),
                        **({'require_native': True} if require_native else {})})
    manifest = {'version': 1, 'catalog_sha256': digest(CATALOG), 'fighters': fighters,
                'scope': 'full_roster' if fighters == available else 'fighter_subset',
                'production_admitted': False, 'cases': entries}
    (output / 'matrix.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return manifest


def load_campaign(campaign):
    manifest = json.loads((campaign / 'matrix.json').read_text())
    if manifest['version'] != 1:
        raise ValueError('unsupported campaign version')
    if manifest['catalog_sha256'] != digest(CATALOG):
        raise ValueError('catalog changed; regenerate campaign')
    available = sorted(set(json.loads(CATALOG.read_text())['fighters'].values()))
    if (not manifest['fighters'] or manifest['fighters'] != sorted(set(manifest['fighters']))
            or set(manifest['fighters']) - set(available)):
        raise ValueError('empty or unknown fighter selection')
    scope = 'full_roster' if manifest['fighters'] == available else 'fighter_subset'
    if manifest['scope'] != scope:
        raise ValueError('campaign scope does not match fighter selection')
    expected = cells(manifest['fighters'])
    if [entry['cell'] for entry in manifest['cases']] != expected:
        raise ValueError('matrix coverage missing, duplicated, or reordered')
    for entry in manifest['cases']:
        path = campaign / 'cases' / (entry['id'] + '.json')
        required = entry.get('require_native', False)
        if type(required) is not bool:
            raise ValueError(f"{entry['id']}: require_native must be boolean")
        if digest(path) != entry['sha256'] or json.loads(path.read_text()) != fixture(entry['cell'], required):
            raise ValueError(f"{entry['id']}: changed input tape")
    return manifest


def validate_trace(case, rows, camera):
    case_id = case['id']
    expected = [(tick, slot) for tick in range(case['frames'] + 1) for slot in ('p1', 'p2')]
    if [(row.get('tick'), row.get('slot')) for row in rows] != expected:
        raise ValueError(f'{case_id}: missing/duplicate/out-of-order fighter observations')
    if [row.get('tick') for row in camera] != list(range(case['frames'] + 1)):
        raise ValueError(f'{case_id}: missing/duplicate/out-of-order camera observations')
    if any(set(row) != STATE_FIELDS for row in rows):
        raise ValueError(f'{case_id}: incomplete fighter state fields')
    if any(set(row) != {'tick', 'x', 'y'} for row in camera):
        raise ValueError(f'{case_id}: incomplete camera fields')
    for row in rows + camera:
        for field in ('x', 'y'):
            value = row.get(field)
            if type(value) not in (int, float) or not float('-inf') < value < float('inf'):
                raise ValueError(f'{case_id}: invalid {field} observation')
    # Inputs latch after the tick-10 observation in move_case_reference.gd.
    start = rows[20]
    if type(start.get('touch')) is not bool:
        raise ValueError(f'{case_id}: missing ground/air observation')
    if start['touch'] != (case['sampling_cell']['posture'] == 'ground'):
        raise ValueError(f'{case_id}: requested posture not reached before input')


def require_native_evidence(entries):
    """Fail closed until a native capture adapter can validate case-bound evidence.

    Godot traces and hand-written success receipts cannot satisfy this reservation.
    Keeping the hook rejecting is intentional; it makes no native parity claim.
    """
    for entry in entries:
        if entry.get('require_native', False):
            raise ValueError(f"{entry['id']}: missing native evidence; "
                             "native capture adapter is not connected")


def run(campaign, output, godot, selected=None):
    manifest = load_campaign(campaign)
    entries = manifest['cases']
    if selected is not None:
        if not selected or len(set(selected)) != len(selected) or set(selected) - {e['id'] for e in entries}:
            raise ValueError('empty, duplicate, or unknown case selection')
        entries = [e for e in entries if e['id'] in selected]
    require_native_evidence(entries)
    output.mkdir(parents=True, exist_ok=False)
    paths = [campaign / 'cases' / (entry['id'] + '.json') for entry in entries]
    results = execute_batch(godot.resolve(), paths, output.resolve())
    errors = []
    for path, result in zip(paths, results):
        try:
            if result['executed'] is not True:
                raise ValueError(f"{result['id']}: execution failed")
            trace = output / (result['id'] + '.json')
            validate_trace(json.loads(path.read_text()), json.loads(trace.read_text()),
                           json.loads(Path(str(trace) + '.presentation.json').read_text()))
        except (ValueError, OSError) as error:
            errors.append(str(error))
    report = {'matrix_sha256': digest(campaign / 'matrix.json'), 'planned': len(manifest['cases']),
              'executed': len(results), 'errors': errors, 'results': results,
              'execution_coverage_complete': len(results) == len(manifest['cases']) and not errors,
              'native_parity_proven': False, 'production_admitted': False}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    if errors:
        raise ValueError('; '.join(errors))
    return report


def require_full_coverage(campaign, output):
    manifest = load_campaign(campaign)
    require_native_evidence(manifest['cases'])
    report = json.loads((output / 'report.json').read_text())
    if report['matrix_sha256'] != digest(campaign / 'matrix.json'):
        raise ValueError('results belong to another campaign')
    if report['errors'] or [r['id'] for r in report['results']] != [e['id'] for e in manifest['cases']]:
        raise ValueError('incomplete matrix execution coverage')
    for entry, result in zip(manifest['cases'], report['results']):
        if result['executed'] is not True:
            raise ValueError(f"{entry['id']}: execution failed")
        path = output / (entry['id'] + '.json')
        validate_trace(fixture(entry['cell']), json.loads(path.read_text()),
                       json.loads(Path(str(path) + '.presentation.json').read_text()))
    return len(manifest['cases'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    gen = sub.add_parser('generate')
    gen.add_argument('--output', type=Path, required=True)
    gen.add_argument('--fighters', nargs='+')
    gen.add_argument('--require-native', action='store_true',
                     help='Reserve native evidence for every case; currently rejects until capture is wired')
    execute = sub.add_parser('run')
    execute.add_argument('--campaign', type=Path, required=True)
    execute.add_argument('--output', type=Path, required=True)
    execute.add_argument('--godot', type=Path, required=True)
    execute.add_argument('--cases', nargs='+')
    check = sub.add_parser('check')
    check.add_argument('--campaign', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'generate':
            print('MATRIX_GENERATED', len(generate(args.output, args.fighters, args.require_native)['cases']))
        elif args.command == 'run':
            report = run(args.campaign.resolve(), args.output.resolve(), args.godot, args.cases)
            print('MATRIX_EXECUTED', report['executed'], 'of', report['planned'], 'native_parity_proven=false')
        else:
            print('MATRIX_EXECUTION_COVERAGE_OK', require_full_coverage(args.campaign, args.output))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'sampling matrix error: {error}\n')


if __name__ == '__main__':
    main()
