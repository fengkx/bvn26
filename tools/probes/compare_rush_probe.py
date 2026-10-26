#!/usr/bin/env python3
"""Compare complete post-frame XG_rush captures without pixel tolerance."""
import argparse
import json
from pathlib import Path


def native_rows(text: str) -> list[dict]:
    rows, runs = {}, set()
    done = False
    for line in text.splitlines():
        if not line.startswith('AIREF|'):
            continue
        fields = line.split('|')
        if len(fields) != 8:
            raise ValueError('Malformed native record')
        runs.add(fields[1])
        tick, kind, payload = int(fields[4]), fields[6], fields[7]
        if kind == 'done':
            done = payload == 'ok'
            continue
        key = 'frame' if kind == 'clock' else kind
        if key not in ('frame', 'pixels') or key in rows.setdefault(tick, {'tick': tick}):
            raise ValueError('Unknown or duplicated native sample')
        rows[tick][key] = int(payload) if key == 'frame' else [int(x) for x in payload.rstrip(',').split(',')]
    if not done or len(runs) != 1 or sorted(rows) != list(range(21)):
        raise ValueError('Incomplete or mixed native capture')
    result = [rows[tick] for tick in range(21)]
    validate_rows(result)
    return result


def validate_rows(rows: list[dict]) -> None:
    if [r['tick'] for r in rows] != list(range(21)):
        raise ValueError('Missing or reordered ticks')
    for row in rows:
        if 'frame' not in row or len(row.get('pixels', [])) != 81:
            raise ValueError('Missing clock or pixel samples')
        if any(type(p) is not int or not 0 <= p <= 0xffffff for p in row['pixels']):
            raise ValueError('Invalid RGB sample')


def compare(expected: list[dict], actual: list[dict]) -> dict:
    validate_rows(expected)
    validate_rows(actual)
    rows = []
    for native, port in zip(expected, actual):
        errors = [abs(((a >> shift) & 255) - ((b >> shift) & 255))
                  for a, b in zip(native['pixels'], port['pixels']) for shift in (16, 8, 0)]
        rows.append({'tick': native['tick'], 'native_frame': native['frame'], 'godot_frame': port['frame'],
                     'different_channels': sum(e != 0 for e in errors), 'max_error': max(errors)})
    return {'passed': all(r['native_frame'] == r['godot_frame'] and r['different_channels'] == 0 for r in rows),
            'clock_matches': sum(r['native_frame'] == r['godot_frame'] for r in rows),
            'clock_samples': len(rows), 'channel_samples': len(rows) * 81 * 3, 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-log', type=Path, required=True)
    parser.add_argument('--godot-rows', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(native_rows(args.native_log.read_text()), json.loads(args.godot_rows.read_text()))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))
    raise SystemExit(0 if result['passed'] else 1)
