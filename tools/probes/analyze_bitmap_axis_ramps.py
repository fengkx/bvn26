#!/usr/bin/env python3
"""Separate bitmap axes and measure native span context without admitting a sampler."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

MODELS = ('byte_weights', 'separable', 'split_initialization')


def identities():
    return [(mode, scale, tx, ty, start, length)
            for mode in range(4) for scale in (2.5, 5, 8)
            for tx in (-.5, .75) for ty in (.25, -.25)
            for start in (1, 3, 4, 5, 17, 253) for length in (1, 3, 4, 5, 7, 8)]


def texel(mode, x, y):
    size = 1024 if mode == 0 else 2 if mode == 1 else 4
    if mode % 2 == 0:
        x, y = max(0, min(size-1, x)), max(0, min(size-1, y))
    else:
        x, y = x % size, y % size
    if mode < 2:
        return (255*(x % 2), 255*(y % 2), 113)
    return ((17, 223, 61, 149)[x], (29, 197, 83, 241)[y], 113)


def split_coordinates(scale, tx, ty, start, y, offset=0):
    inverse = math.floor(65536/scale+.5)
    half = math.floor(inverse/2+.5)
    return ((math.floor((start-tx)/scale*65536)+half+offset*inverse)/65536-.5,
            (math.floor((y-ty)/scale*65536)+half)/65536-.5)


def predict(identity, offset, model):
    mode, scale, tx, ty, start, _ = identity
    inverse = math.floor(65536/scale+.5)
    x = (start+offset+.5-tx)*inverse/65536-.5
    y = (4.5-ty)*inverse/65536-.5
    if model == 'split_initialization':
        # Rejected by the independent r22/r24 suites; never a production rule.
        x, y = split_coordinates(scale, tx, ty, start, 4, offset)
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = math.floor((x-ix)*256), math.floor((y-iy)*256)
    colors = [texel(mode, ix+dx, iy+dy) for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))]
    if model == 'separable':
        left = [(colors[0][k]*(256-fy)+colors[2][k]*fy)//256 for k in range(3)]
        right = [(colors[1][k]*(256-fy)+colors[3][k]*fy)//256 for k in range(3)]
        return [(left[k]*(256-fx)+right[k]*fx)//256 for k in range(3)]
    weights = [(256-fx)*(256-fy)//256, fx*(256-fy)//256, (256-fx)*fy//256]
    weights.append(256-sum(weights))
    return [sum(w*c[k] for w, c in zip(weights, colors))//256 for k in range(3)]


def analyze(text):
    expected = identities()
    events = [line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    if (len(events) != len(expected)+1 or any(len(e) != 8 for e in events)
            or len({e[1] for e in events}) != 1
            or not events[0][1].startswith('filter-bitmap-axis-ramps-r26-')
            or [int(e[2]) for e in events] != list(range(len(events)))
            or events[-1][6:] != ['done', 'ok']):
        raise ValueError('Incomplete, mixed or duplicate axis capture')
    rows = []
    for event, identity in zip(events, expected):
        values = event[7].split(',')
        if (event[6] != 'axis' or len(values) != 6+identity[-1]
                or tuple(map(float, values[:6])) != identity):
            raise ValueError('Axis identity/sample count mismatch')
        pixels = list(map(int, values[6:]))
        if any(not 0 <= pixel <= 0xffffff for pixel in pixels):
            raise ValueError('Invalid RGB pixel')
        for offset, pixel in enumerate(pixels):
            rows.append({'identity': identity, 'offset': offset, 'x': identity[4]+offset, 'y': 4,
                         'native_rgb': [(pixel >> shift) & 255 for shift in (16, 8, 0)],
                         'predictions': {m: predict(identity, offset, m) for m in MODELS}})
    scores = []
    for mode in range(4):
        for length in (1, 3, 4, 5, 7, 8):
            group = [r for r in rows if r['identity'][0] == mode and r['identity'][-1] == length]
            for model in MODELS:
                scores.append({'mode': mode, 'length': length, 'model': model, 'samples': len(group),
                               'exact': sum(r['native_rgb'] == r['predictions'][model] for r in group),
                               'max_delta': max(abs(a-b) for r in group
                                                for a, b in zip(r['native_rgb'], r['predictions'][model]))})
    scalar = defaultdict(list)
    singles = {}
    for row in rows:
        key = (*row['identity'][:4], row['x'])
        if row['identity'][-1] < 4:
            scalar[key].append(row)
        if row['identity'][-1] == 1:
            singles[key] = row['native_rgb']
    controls = []
    for key, group in scalar.items():
        if len(group) > 1:
            controls.append({'key': key, 'samples': len(group),
                             'exact': len({tuple(r['native_rgb']) for r in group}) == 1})
    context = []
    compared = 0
    for row in rows:
        key = (*row['identity'][:4], row['x'])
        if key not in singles:
            continue
        compared += 1
        if row['native_rgb'] != singles[key]:
            context.append({'identity': row['identity'], 'offset': row['offset'], 'x': row['x'],
                            'single_rgb': singles[key], 'span_rgb': row['native_rgb']})
    exact_models = [model for model in MODELS
                    if all(s['exact'] == s['samples'] for s in scores if s['model'] == model)]
    return {'production_admitted': False, 'passed': bool(exact_models), 'exact_models': exact_models,
            'native_rows': len(expected), 'samples': len(rows),
            'constant_channel_exact': sum(r['native_rgb'][2] == 113 for r in rows),
            'scores': scores, 'scalar_overlap_controls': controls,
            'single_coordinate_comparisons': compared, 'context_differences': context, 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-log', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native_log.read_text())
    rows = result.pop('rows')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    args.output.with_suffix('.jsonl').write_text(''.join(json.dumps(r, separators=(',', ':'))+'\n' for r in rows))
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('scores', 'scalar_overlap_controls', 'context_differences')}))
    raise SystemExit(0 if result['passed'] else 1)
