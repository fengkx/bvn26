#!/usr/bin/env python3
"""Measure short-span context dependence; no production sampler admission."""
import argparse
import json
import math
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.probes.analyze_bitmap_inverse import COLORS


def identities():
    for mode in (0, 1):
        for suite in (0, 1):
            for scale in (2.5, 5, 8):
                for tx in ([i/8 for i in range(-8, 9)] if suite == 0 else [-.5, .75]):
                    for ty in ([.25, -.25] if suite == 0 else [.25]):
                        for start in (range(3, 9) if suite == 0 else [0, 1, 3, 4, 5, 17, 253]):
                            for length in ([1] if suite == 0 else range(1, 9)):
                                yield suite, mode, scale, tx, ty, start, length


def predict(mode, scale, tx, ty, start, offset, model):
    tx, ty = math.trunc(tx*4)/4, math.trunc(ty*4)/4
    inverse = math.floor(65536/scale + .5)/65536
    x = (start+offset+.5-tx)*inverse-.5
    y = (4.5-ty)*inverse-.5
    if model == 'exact_inverse':
        x, y = (start+offset+.5-tx)/scale-.5, (4.5-ty)/scale-.5
    elif model == 'exact_initialization':
        x, y = (start+.5-tx)/scale-.5+offset*inverse, (4.5-ty)/scale-.5
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = math.floor((x-ix)*256), math.floor((y-iy)*256)
    colors = []
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        sx, sy = ix+dx, iy+dy
        if mode == 0:
            sx, sy = max(0, min(1023, sx)), max(0, min(1023, sy))
        colors.append(COLORS[sy % 2][sx % 2])
    weights = [(256-fx)*(256-fy)//256, fx*(256-fy)//256, (256-fx)*fy//256]
    weights.append(256-sum(weights))
    return [sum(w*c[k]*255 for w, c in zip(weights, colors))//256 for k in range(3)]


def analyze(text):
    expected = list(identities())
    events = [line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    if (len(events) != len(expected)+1 or any(len(e) != 8 for e in events)
            or len({e[1] for e in events}) != 1
            or not events[0][1].startswith('filter-bitmap-short-spans-r25-')
            or [int(e[2]) for e in events] != list(range(len(events)))
            or events[-1][6:] != ['done', 'ok']):
        raise ValueError('Incomplete, mixed or duplicate native short-span capture')
    rows, first_pixels = [], {}
    for event, identity in zip(events, expected):
        values = event[7].split(',')
        suite, mode, scale, tx, ty, start, length = identity
        if (event[6] != 'short' or len(values) != 7+length
                or tuple(map(float, values[:7])) != identity):
            raise ValueError('Native short-span identity/sample count mismatch')
        pixels = list(map(int, values[7:]))
        if any(not 0 <= pixel <= 0xffffff for pixel in pixels):
            raise ValueError('Invalid RGB pixel')
        for offset, pixel in enumerate(pixels):
            native = [(pixel >> shift) & 255 for shift in (16, 8, 0)]
            predictions = {model: predict(mode, scale, tx, ty, start, offset, model)
                           for model in ('quantized_inverse', 'exact_inverse', 'exact_initialization')}
            rows.append({'identity': identity, 'x': start+offset, 'y': 4,
                         'geometry_interior': start+offset >= math.ceil(tx),
                         'native_rgb': native, 'predictions': predictions})
        if suite == 1:
            first_pixels.setdefault((mode, scale, tx, ty, start), {})[length] = pixels[0]
    controls = []
    for key, pixels in first_pixels.items():
        controls.append({'identity': key,
                         'first_rgb_by_length': [[(pixels[n] >> s) & 255 for s in (16, 8, 0)]
                                                 for n in range(1, 9)],
                         'changed_lengths': [n for n in range(2, 9) if pixels[n] != pixels[1]]})
    scores = []
    for suite in (0, 1):
        for mode in (0, 1):
            group = [r for r in rows if r['identity'][:2] == (suite, mode) and r['geometry_interior']]
            for model in ('quantized_inverse', 'exact_inverse', 'exact_initialization'):
                scores.append({'suite': suite, 'mode': mode, 'model': model, 'samples': len(group),
                               'exact': sum(r['native_rgb'] == r['predictions'][model] for r in group),
                               'max_delta': max(abs(a-b) for r in group
                                                for a, b in zip(r['native_rgb'], r['predictions'][model]))})
    clipped = {r['identity'][2:]: r for r in rows if r['identity'][:2] == (0, 0)}
    mode_differences = []
    for row in rows:
        if row['identity'][:2] != (0, 1):
            continue
        other = clipped[row['identity'][2:]]
        if row['native_rgb'] != other['native_rgb']:
            mode_differences.append({'identity': row['identity'][2:],
                                     'clipped_rgb': other['native_rgb'], 'repeat_rgb': row['native_rgb']})
    exact_models = [model for model in ('quantized_inverse', 'exact_inverse', 'exact_initialization')
                    if all(s['exact'] == s['samples'] for s in scores if s['model'] == model)]
    return {'production_admitted': False, 'passed': bool(exact_models), 'exact_models': exact_models,
            'native_rows': len(expected), 'samples': len(rows),
            'geometry_fringe_samples': sum(not r['geometry_interior'] for r in rows), 'scores': scores,
            'first_pixel_controls': controls, 'single_pixel_mode_differences': mode_differences, 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-log', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.native_log.read_text())
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('rows', 'first_pixel_controls')}))
    raise SystemExit(0 if report['passed'] else 1)
