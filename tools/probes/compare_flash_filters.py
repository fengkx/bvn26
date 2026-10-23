#!/usr/bin/env python3
"""Compare GPU samples to native Flash trace rows without a parity tolerance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def native_rows(log: str, kind: str) -> list[dict]:
    rows = []
    color_kind = kind in ('color', 'color-order')
    event_kind = 'color' if color_kind else kind
    black_rows = []
    run_ids = set()
    done = False
    for line in log.splitlines():
        if not line.startswith('AIREF|'):
            continue
        parts = line.split('|')
        if len(parts) != 8:
            raise ValueError('Malformed native filter record')
        run_ids.add(parts[1])
        if parts[6] == 'done' and parts[7] == 'ok':
            done = True
        elif color_kind and parts[6] == 'black':
            name, opacity, *pixels = parts[7].split(',')
            black_rows.append({'type': name, 'opacity': int(opacity),
                               'pixels': [int(p) & 0xffffffff for p in pixels]})
        elif parts[6] == event_kind:
            values = parts[7].split(',')
            if kind == 'bounds':
                width, first, second, *pixels = values
            else:
                first, second, *pixels = values
            if kind in ('blur', 'bounds'):
                rows.append({'size': int(first), 'passes': int(second),
                             'alpha': [(int(p) >> 24) & 255 for p in pixels]})
                if kind == 'bounds':
                    rows[-1]['width'] = int(width)
            else:
                rows.append({'type': first, 'opacity': int(second),
                             'pixels': [int(p) & 0xffffffff for p in pixels]})
    if not done or len(run_ids) != 1 or not rows:
        raise ValueError('Incomplete or mixed native capture')
    expected_keys = ([(size, passes) for size in (0, 1, 2, 3, 5, 10, 15, 20)
                      for passes in (1, 3)] if kind == 'blur' else
                     [('glow', 100), ('glow', 50), ('matrix', 100), ('matrix', 50), ('chain', 100)])
    if kind == 'color-order':
        expected_keys = expected_keys[:4]
    if kind == 'bounds':
        expected_keys = [(w, n, q) for w in (1, 2, 4, 8, 12, 16, 32)
                         for n in (6, 7, 8, 9, 10, 11, 15, 20, 21, 30) for q in (1, 2, 3)]
        keys = [(r['width'], r['size'], r['passes']) for r in rows]
    else:
        keys = [(r['size'], r['passes']) if kind == 'blur' else (r['type'], r['opacity']) for r in rows]
    if keys != expected_keys:
        raise ValueError('Missing, duplicated or reordered native cases')
    if color_kind:
        if [(r['type'], r['opacity']) for r in black_rows] != expected_keys:
            raise ValueError('Missing, duplicated or reordered native black-background cases')
        for row, black in zip(rows, black_rows):
            if len(row['pixels']) != len(black['pixels']) or any(p >> 24 != 255 for p in black['pixels']):
                raise ValueError('Invalid native black-background samples')
            row['premultiplied'] = [[(p >> shift) & 255 for shift in (16, 8, 0)]
                                    + [(alpha >> 24) & 255]
                                    for p, alpha in zip(black['pixels'], row['pixels'])]
    return rows


def compare(native: list[dict], actual: list[dict], kind: str) -> dict:
    if len(native) != len(actual):
        raise ValueError('Native/Godot case counts differ')
    results = []
    for expected, measured in zip(native, actual):
        keys = ('size', 'passes') if kind == 'blur' else ('type', 'opacity')
        if kind == 'bounds':
            keys = ('width', 'size', 'passes')
        case = {key: expected[key] for key in keys}
        if any(measured.get(key) != expected[key] for key in keys):
            raise ValueError(f'Native/Godot case identity differs: {case}')
        if kind in ('blur', 'bounds'):
            reference, observed = expected['alpha'], measured['alpha']
        else:
            # Reconstructing premultiplied channels from getPixel32 loses bits.
            # Use the separately captured native black-background RGB instead.
            if 'premultiplied' not in expected:
                raise ValueError('Color comparison requires native black-background samples')
            reference = [channel for pixel in expected['premultiplied'] for channel in pixel]
            observed = [channel for pixel in measured['pixels'] for channel in pixel]
        if not reference or len(reference) != len(observed):
            raise ValueError(f'Native/Godot sample counts differ: {case}')
        errors = [abs(a - b) for a, b in zip(reference, observed)]
        results.append({**case, 'samples': len(errors), 'different': sum(e != 0 for e in errors),
                        'max_error': max(errors)})
    return {'passed': all(r['different'] == 0 for r in results), 'cases': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-log', type=Path, required=True)
    parser.add_argument('--godot-rows', type=Path, required=True)
    parser.add_argument('--kind', choices=['blur', 'bounds', 'color', 'color-order'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(native_rows(args.native_log.read_text(), args.kind),
                     json.loads(args.godot_rows.read_text()), args.kind)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['passed'] else 1)
