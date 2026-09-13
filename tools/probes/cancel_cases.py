"""Calibrate one-tick cancellation inputs from retained original root observations."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from compare_mode_reference import source_rows
from move_cases import COMMANDS, ROOT, window

CANCEL_COMMANDS = dict(COMMANDS, standup=['dash'])
# Sprite 14's standup() reads kis(_parent.冲), the source dash binding.

def same_window_route(rows, index, source):
    frame = rows[index]['frame']
    start, end = source['start_frame'], source['end_frame']
    if start <= frame <= end:
        return True
    adjacent = rows[index + 1:] if frame < start else reversed(rows[:index])
    neighbor = next((row['frame'] for row in adjacent if row['frame'] != frame), None)
    return neighbor is not None and start <= neighbor <= end


def apply_source_target(case, source_window, source_action):
    """Bind the fixture target to the window's actual source action."""
    start = source_action.get('start_frame')
    end = source_action.get('end_frame')
    if not isinstance(start, int) or not isinstance(end, int) or start > end:
        raise ValueError(f"Cancel source action has no valid timeline: {source_window['from']}")
    window_start = source_window.get('start_frame')
    window_end = source_window.get('end_frame')
    if not isinstance(window_start, int) or not isinstance(window_end, int):
        raise ValueError('Cancel window has invalid source frames')
    if window_start < start or window_end > end + 1:
        raise ValueError(
            f"Cancel window {source_window['from']} {window_start}-{window_end} "
            f"does not belong to source action frames {start}-{end}"
        )

    case['label'] = source_action['label']
    case['target_frames'] = [start, end]
    case['has_source_timeline'] = source_action.get('has_timeline', False)
    case['source_dispatch'] = source_action.get('source_dispatch', [])
    case['source_target'] = {
        key: source_action.get(key)
        for key in ('label', 'start_frame', 'end_frame', 'implementation',
                    'has_timeline', 'source_dispatch', 'contexts', 'energy_min')
    }
    return [start, end]


def generate(fighter, references):
    model = json.loads((ROOT / f'godot/generated/fighters/{fighter}/combat.json').read_text())
    entries = {entry['label']: entry for entry in model['command_catalog']['entries']}
    calibrations = []
    folders = [folder for root in references for folder in root.iterdir()]
    for folder in sorted(folders):
        fixture_path = folder / 'case.json'
        if not fixture_path.exists():
            continue
        fixture = json.loads(fixture_path.read_text())
        if fixture['fighter'] != fighter or 'window_boundary' in fixture:
            continue
        events = folder / 'events.jsonl'
        rows = [row for row in source_rows(events) if row['slot'] == fixture['slot']]
        calibrations.append((fixture, events, rows))
    calibrations.sort(key=lambda item: item[0]['scenario'] != 'neutral')
    cases, unavailable = [], []
    for index, source in enumerate(model['command_catalog']['cancel_windows']):
        for edge, frame in [('before_start', source['start_frame'] - 1),
                            ('at_start', source['start_frame']),
                            ('at_end', source['end_frame']),
                            ('after_end', source['end_frame'] + 1)]:
            identifier = f'{fighter}-window-{index}-{edge}'
            if source['predicate'] not in CANCEL_COMMANDS:
                unavailable.append({'id': identifier, 'reason': 'source calibration route required'})
                continue
            calibration = next(((fixture, events, row) for fixture, events, rows in calibrations
                                for i, row in enumerate(rows)
                                if row['frame'] == frame and same_window_route(rows, i, source)), None)
            if calibration is None:
                unavailable.append({'id': identifier, 'reason': 'boundary frame absent in calibration'})
                continue
            fixture, events, observation = calibration
            case = copy.deepcopy(fixture)
            source_action = entries.get(source['from'])
            if source_action is None or not source_action.get('has_timeline'):
                unavailable.append({'id': identifier, 'reason': 'cancel source action has no timeline'})
                continue
            tick = observation['tick']
            # The observer records state before publishing keys for the next callbacks.
            case['id'] = identifier
            case['scenario'] = 'cancel_' + edge
            # Keep the calibrated prefix, then publish only the one-tick follow-up.
            case['inputs'] = [dict(item, end=min(item['end'], tick)) for item in case['inputs']
                              if item['start'] < tick]
            case['inputs'].append(window(case['slot'], CANCEL_COMMANDS[source['predicate']], tick, tick + 1))
            case['window_boundary'] = {'id': identifier, 'window_index': index, 'edge': edge,
                                       'source_frame': frame, 'input_tick': tick, 'window': source}
            case['window_boundary']['source_action_frames'] = apply_source_target(
                case, source, source_action)
            case['window_boundary']['source_action'] = source_action['label']
            destination = next(entry for entry in model['command_catalog']['entries']
                               if entry['label'] == source['to'])
            case['window_boundary']['destination_frames'] = [destination['start_frame'], destination['end_frame']]
            case['calibration'] = {'case_id': fixture['id'],
                                   'events_sha256': hashlib.sha256(events.read_bytes()).hexdigest(),
                                   'observer_phase': 'root state before input publication'}
            cases.append(case)
    return cases, unavailable


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fighter', required=True)
    parser.add_argument('--references', type=Path, action='append', required=True)
    parser.add_argument('--exclude-cases', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases, unavailable = generate(args.fighter, args.references)
    if args.exclude_cases:
        existing = {p.stem for p in args.exclude_cases.glob('*.json')}
        cases = [case for case in cases if case['id'] not in existing]
    args.output.mkdir(parents=True, exist_ok=False)
    for case in cases:
        (args.output / (case['id'] + '.json')).write_text(json.dumps(case, ensure_ascii=False, indent=2) + '\n')
    args.output.with_suffix('.unavailable.json').write_text(json.dumps(unavailable, indent=2) + '\n')
    print(json.dumps({'calibrated_not_accepted': len(cases), 'calibration_required': len(unavailable)}))


if __name__ == '__main__':
    main()
