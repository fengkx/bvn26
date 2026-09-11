"""Compare source helper_state events with native helper snapshots.

The source side uses the same canonical fight_tick cutoff as
``compare_mode_reference``.  Helper snapshots have deliberately different
schemas, so the report names the orientation unit conversion and records
fields that cannot be compared instead of treating them as equal.
"""
import argparse
import gzip
import json
from pathlib import Path

try:
    from collect_ai_reference import decode_number
except ModuleNotFoundError:  # Import also works as tools.probes.compare_helper_reference.
    from tools.probes.collect_ai_reference import decode_number


SOURCE_FIELDS = [
    'frame', 'x', 'y', 'xscale', 'attacking', 'action', 'hits',
    'atm1', 'atm2', 'atm3',
]
NATIVE_FIELDS = ['tick', 'slot', 'frame', 'x', 'y', 'action', 'attacking', 'facing']
COMPARISONS = [
    {'name': 'frame', 'source': 'frame', 'native': 'frame', 'transform': 'identity'},
    {'name': 'x', 'source': 'x', 'native': 'x', 'transform': 'identity'},
    {'name': 'y', 'source': 'y', 'native': 'y', 'transform': 'identity'},
    {
        'name': 'orientation',
        'source': 'xscale',
        'native': 'facing',
        'transform': 'source xscale percent / 100 = native facing sign',
    },
    {'name': 'action', 'source': 'action', 'native': 'action', 'transform': 'identity'},
    {
        'name': 'attacking',
        'source': 'attacking',
        'native': 'attacking',
        'transform': 'identity',
    },
]


def read_text(path: Path) -> str:
    if path.suffix == '.gz':
        with gzip.open(path, 'rt', encoding='utf-8') as stream:
            return stream.read()
    return path.read_text(encoding='utf-8')


def decode_value(value: str):
    if value == 'undefined':
        return None
    if value in ('true', 'false'):
        return value == 'true'
    return decode_number(value)


def source_rows(events: Path) -> list[dict]:
    rows = []
    for line in read_text(events).splitlines():
        event = json.loads(line)
        # Keep the root observation convention shared with fighter comparison.
        if event['kind'] != 'helper_state' or event['fight_tick'] < 0:
            continue
        values = event['value'].split(',')
        if len(values) != len(SOURCE_FIELDS) + 1:
            raise ValueError('Unexpected helper state shape')
        row = {
            'tick': event['fight_tick'],
            'slot': values[0],
            'source_raw_value': event['value'],
        }
        for key, value in zip(SOURCE_FIELDS, values[1:]):
            row[key] = decode_value(value)
        rows.append(row)
    return rows


def native_rows(native: Path) -> list[dict]:
    rows = json.loads(read_text(native))
    if not isinstance(rows, list):
        raise ValueError('Native helper snapshots must be a JSON array')
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(NATIVE_FIELDS):
            raise ValueError('Native helper fields do not match expected snapshot shape')
    return rows


def _field_values(source: dict, native: dict) -> list[tuple[str, object, object]]:
    return [
        ('frame', source['frame'], native['frame']),
        ('x', source['x'], native['x']),
        ('y', source['y'], native['y']),
        ('orientation', source['xscale'], native['facing']),
        ('action', source['action'], native['action']),
        ('attacking', source['attacking'], native['attacking']),
    ]


def compare(events: Path, native: Path) -> dict:
    expected = source_rows(events)
    actual = native_rows(native)
    differences = []
    for source, port in zip(expected, actual):
        if (source['tick'], source['slot']) != (port['tick'], port['slot']):
            differences.append({
                'tick': source['tick'],
                'slot': source['slot'],
                'field': 'alignment',
                'source': {'tick': source['tick'], 'slot': source['slot']},
                'native': {'tick': port['tick'], 'slot': port['slot']},
            })
            continue
        for field, original, port_value in _field_values(source, port):
            expected_value = original / 100 if field == 'orientation' and original is not None else original
            if expected_value != port_value:
                differences.append({
                    'tick': source['tick'],
                    'slot': source['slot'],
                    'field': field,
                    'source_value': original,
                    'native_value': port_value,
                    'source_normalized': expected_value,
                })

    compared = min(len(expected), len(actual))
    first_difference = None
    if differences:
        first = differences[0]
        index = next(
            i for i, (source, port) in enumerate(zip(expected, actual))
            if source['tick'] == first['tick'] and source['slot'] == first['slot']
        )
        first_difference = {
            **first,
            'source_raw_row': expected[index],
            'native_raw_row': actual[index],
        }
    active = {
        side: {
            slot: sum(row.get('attacking') is True for row in rows if row['slot'] == slot)
            for slot in ('p1', 'p2')
        }
        for side, rows in [('source', expected), ('native', actual)]
    }
    active_boundaries = {}
    for slot in ('p1', 'p2'):
        source_active = next((row for row in expected
                              if row['slot'] == slot and row['attacking'] is True), None)
        native_active = next((row for row in actual
                              if row['slot'] == slot and row['attacking'] is True), None)
        source_tick = source_active['tick'] if source_active else None
        native_at_source_tick = next(
            (row for row in actual if row['slot'] == slot and row['tick'] == source_tick),
            None,
        )
        active_boundaries[slot] = {
            'source_first_active': source_active,
            'native_at_source_first_active_tick': native_at_source_tick,
            'native_first_active': native_active,
        }
    return {
        'status': 'matched' if expected and len(expected) == len(actual) and not differences else 'different',
        'source_rows': len(expected),
        'native_rows': len(actual),
        'complete': bool(expected) and len(expected) == len(actual),
        'canonical_tick_filter': 'helper_state events with fight_tick >= 0; no offset',
        'fields_compared': COMPARISONS,
        'source_only_fields': ['hits', 'atm1', 'atm2', 'atm3'],
        'native_only_fields': [],
        'active_row_counts': active,
        'active_boundaries': active_boundaries,
        'compared_rows': compared,
        'difference_count': len(differences),
        'differences': differences,
        'first_difference': first_difference,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('events', type=Path)
    parser.add_argument('native', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.events, args.native)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'source_rows', 'native_rows', 'difference_count')}))
    raise SystemExit(0 if result['status'] == 'matched' else 1)


if __name__ == '__main__':
    main()
