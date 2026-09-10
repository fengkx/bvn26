"""Compare both source fighters at every root observation, without tolerances."""
import argparse
import gzip
import json
from pathlib import Path

from collect_ai_reference import decode_number

FIELDS = ['frame', 'x', 'y', 'xscale', 'action', 'hp', 'ql', 'sw', 'touch',
          'touchFloor', 'hits', 'paused', 'hstm', 'hurtSkling']


def read_text(path: Path) -> str:
    if path.suffix == '.gz':
        with gzip.open(path, 'rt', encoding='utf-8') as stream:
            return stream.read()
    return path.read_text()


def source_rows(events: Path) -> list[dict]:
    expected = []
    for line in read_text(events).splitlines():
        event = json.loads(line)
        if event['kind'] != 'state' or event['fight_tick'] < 0:
            continue
        values = event['value'].split(',')
        if len(values) != len(FIELDS) + 1:
            raise ValueError('Unexpected fighter state shape')
        row = {'tick': event['fight_tick'], 'slot': values[0]}
        for key, value in zip(FIELDS, values[1:]):
            row[key] = (None if value == 'undefined' else json.loads(value)
                        if value in ['true', 'false'] else decode_number(value))
        expected.append(row)
    return expected


def compare(events: Path, native: Path) -> dict:
    expected = source_rows(events)
    actual = json.loads(read_text(native))
    differences = []
    for original, port in zip(expected, actual):
        if set(port) != set(original):
            raise ValueError('Native state fields do not match source fields')
        changes = {key: {'original': original[key], 'native': port[key]}
                   for key in original if original[key] != port[key]}
        if changes:
            differences.append({'tick': original['tick'], 'slot': original['slot'], 'fields': changes})
    complete = bool(expected) and len(expected) == len(actual)
    return {'status': 'matched' if complete and not differences else 'different',
            'source_states': len(expected), 'native_states': len(actual),
            'complete': complete, 'fields': FIELDS, 'differences': differences}


def compare_root_position(events: Path, native: Path) -> dict:
    expected = []
    for line in read_text(events).splitlines():
        event = json.loads(line)
        if event['kind'] != 'root_position' or event['fight_tick'] < 0:
            continue
        x, y = map(decode_number, event['value'].split(','))
        expected.append({'tick': event['fight_tick'], 'x': x, 'y': y})
    actual = json.loads(read_text(native))
    differences = [{'source': a, 'native': b} for a, b in zip(expected, actual) if a != b]
    complete = bool(expected) and len(expected) == len(actual)
    return {'status': 'matched' if complete and not differences else 'different',
            'source_rows': len(expected), 'native_rows': len(actual),
            'differences': differences}


def cancellation_observation(rows: list[dict], case: dict) -> dict:
    boundary = case['window_boundary']
    actor = [row for row in rows if row['slot'] == case['slot']]
    at_input = next((row for row in actor if row['tick'] == boundary['input_tick']), None)
    calibrated = at_input is not None and at_input['frame'] == boundary['source_frame']
    low, high = boundary['destination_frames']
    destination = next((row['tick'] for row in actor if row['tick'] > boundary['input_tick']
                        and low is not None and low <= row['frame'] <= high), None)
    return {'status': 'calibrated' if calibrated else 'invalid_calibration',
            'input_frame': at_input['frame'] if at_input else None,
            'destination_first_observed_tick': destination}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('events', type=Path)
    parser.add_argument('native', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.events, args.native)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['status', 'source_states', 'native_states']}))
    raise SystemExit(0 if result['status'] == 'matched' else 1)


if __name__ == '__main__':
    main()
