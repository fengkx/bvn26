#!/usr/bin/env python3
"""Test the near-origin bitmap candidate against independent native distance/size probes."""
import argparse
import json
import math
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.probes.analyze_bitmap_phase import candidate, candidate_coordinates

SCALES = (1.01, 1.7, 2.5, 3, 5, 7.99, 8, 13.3)
PHASES = (-224, -128, -32, 0, 32, 128, 224)
POSITIONS = (4, 7, 15, 31, 63, 127, 255, 383, 511)
SIZES = (2, 4, 8, 16, 64, 1024)
COLORS = (((1, 0, 0), (0, 1, 0)), ((0, 0, 1), (1, 1, 1)))


def predict(alpha, scale, phase, px, py, clipped, *, scalar=False):
    x, y = candidate_coordinates(scale, phase, px, py)
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = math.floor((x - ix) * 256), math.floor((y - iy) * 256)
    weights = [(256-fx)*(256-fy)//256, fx*(256-fy)//256, (256-fx)*fy//256]
    weights.append(256 - sum(weights))
    colors = []
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        sx, sy = ix + dx, iy + dy
        if clipped:
            sx, sy = max(0, min(1023, sx)), max(0, min(1023, sy))
        colors.append(COLORS[sy % 2][sx % 2])
    if scalar or (clipped and (ix <= 0 or iy <= 0)):
        return [sum(w*c[channel]*alpha for w, c in zip(weights, colors))//256
                for channel in range(3)]
    # Independent diagnostic hypothesis for interior pixels; not a runtime rule.
    output = []
    for channel in range(3):
        left = (colors[0][channel]*alpha*(256-fy) + colors[2][channel]*alpha*fy)//256
        right = (colors[1][channel]*alpha*(256-fy) + colors[3][channel]*alpha*fy)//256
        output.append((left*(256-fx) + right*fx)//256)
    return output


def analyze(text, kind):
    scalar = kind.startswith('scalar-')
    mode = kind.removeprefix('scalar-')
    size_probe = kind == 'size'
    name = {'size': 'bitmap-size', 'repeat': 'bitmap-inverse',
            'clipped': 'bitmap-inverse-clipped', 'row': 'bitmap-row',
            'scalar-clipped': 'bitmap-scalar-clipped',
            'scalar-repeat': 'bitmap-scalar-repeat'}[kind]
    revision = 'r24' if scalar else 'r23'
    identities = ([(a, size, s, p) for a in (255, 128) for size in SIZES
                   for s in (2.5, 3, 5, 8) for p in (-224, -128, 0, 128, 224)]
                  if size_probe else [(a, s, p) for a in (255, 128)
                                      for s in SCALES for p in PHASES])
    if kind == 'row':
        identities = [(255, s, p) for s in (1.01, 2.5, 5, 8) for p in (-224, 0, 224)]
    events = [line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    if (len(events) != len(identities) + 1 or any(len(e) != 8 for e in events) or
            len({e[1] for e in events}) != 1 or not events[0][1].startswith(f'filter-{name}-{revision}-') or
            [int(e[2]) for e in events] != list(range(len(events))) or events[-1][6:] != ['done', 'ok']):
        raise ValueError('Incomplete, mixed or duplicate native inverse capture')
    rows = []
    sizes = {}
    for event, identity in zip(events, identities):
        values = event[7].split(',')
        count = 1 if size_probe else (504 if kind == 'row' else len(POSITIONS))
        if (event[6] != ('size' if size_probe else 'inverse') or
                len(values) != len(identity) + count or
                tuple(map(float, values[:len(identity)])) != identity):
            raise ValueError('Native inverse identity/sample count mismatch')
        pixels = list(map(int, values[len(identity):]))
        if any(not 0 <= p <= 0xffffff for p in pixels):
            raise ValueError('Invalid native RGB pixel')
        if size_probe:
            alpha, size, scale, phase = identity
            sizes.setdefault((alpha, scale, phase), []).append(pixels[0])
            positions = [(math.floor(scale), math.floor(scale))]
        else:
            alpha, scale, phase = identity
            size = 1024 if mode in ('clipped', 'row') else 2
            positions = ([(px, 155) for px in range(16, 520)] if kind == 'row' else
                         [(px, math.floor(px * .6) + 2) for px in POSITIONS])
        for (px, py), pixel in zip(positions, pixels):
            native = [(pixel >> shift) & 255 for shift in (16, 8, 0)]
            predicted = (candidate(alpha, scale, phase, True) if size_probe else
                         predict(alpha, scale, phase, px, py, mode in ('clipped', 'row'), scalar=scalar))
            rows.append({'alpha': alpha, 'size': size, 'scale': scale, 'phase': phase,
                         'x': px, 'y': py, 'native_rgb': native, 'candidate_rgb': predicted,
                         'max_delta': max(abs(a-b) for a,b in zip(native, predicted))})
    result = {'kind': kind, 'candidate_only': True, 'production_admitted': False,
              'samples': len(rows), 'exact': sum(r['max_delta'] == 0 for r in rows),
              'max_delta': max(r['max_delta'] for r in rows),
              'passed': all(r['max_delta'] == 0 for r in rows), 'rows': rows}
    if size_probe:
        result['size_control_groups'] = len(sizes)
        result['size_control_exact'] = sum(len(set(pixels)) == 1 for pixels in sizes.values())
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-log', type=Path, required=True)
    parser.add_argument('--kind', choices=('repeat', 'clipped', 'size', 'row', 'scalar-clipped', 'scalar-repeat'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native_log.read_text(), args.kind)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))
    raise SystemExit(0 if result['passed'] else 1)
