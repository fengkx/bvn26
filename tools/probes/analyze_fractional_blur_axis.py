"""Reject globally defined blur arithmetic against explicit native source readbacks."""
import argparse
import hashlib
import json
import itertools
import math
from pathlib import Path
from tools.probes.run_nested_filters import unpack

ROOT = Path(__file__).resolve().parents[2]
MODELS = ('rational', 'weight8', 'reciprocal16', 'weight8_reciprocal16', 'weight8_renormalized')


def decode(native):
    build = json.loads((native / 'build.json').read_text())
    assert hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest() == build['source_sha256']
    events = [s.split('|') for s in (native / 'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    assert len(events) == 946 and events[-1][6:] == ['done', 'ok']
    for i, row in enumerate(events):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    result = []
    grid = itertools.product((3.5, 3.99609375, 4, 4.00390625, 7.5, 7.99609375, 8),
                             (1, 25, 135, 204, 255), range(3), range(3))
    for i, (kernel, alpha, pattern, axis) in enumerate(grid):
        rows = events[i*3:i*3+3]
        assert rows[0][6] == 'case'
        key = list(map(float, rows[0][7].split(',')))
        assert key == [i, kernel, alpha, pattern, axis,
                       1 if axis == 1 else kernel, 1 if axis == 0 else kernel]
        case = {'key': key}
        for row, stage in zip(rows[1:], ('input', 'filtered')):
            values = row[7].split(',')
            assert row[6] == 'row' and values[:2] == [str(i), stage] and len(values) == 66
            case[stage] = unpack(list(map(int, values[2:])))
        result.append(case)
    return result


def source(alpha, pattern):
    return [[(alpha if pattern == 0 else (alpha if x == y == 16 else 0) if pattern == 1 else alpha*(x-8)//16)
             if 8 <= x < 25 and 8 <= y < 25 else 0 for x in range(32)] for y in range(32)]


def axis_pass(image, kernel, vertical, model):
    if kernel <= 1:
        return image
    radius = (round(kernel*256)-256)  # Radius in units of 1/512.
    weights = [(i, min(512, max(0, radius-abs(i)*512+512)))
               for i in range(-math.ceil(radius/512), math.ceil(radius/512)+1)]
    if model.startswith('weight8'):
        weights = [(i, w//2*2) for i, w in weights]
    denom = round(kernel*512)
    if model == 'weight8_renormalized':
        denom = sum(w for _, w in weights)
    reciprocal = math.floor(65536/kernel)
    output = []
    for y in range(32):
        row = []
        for x in range(32):
            total = 0
            for i, w in weights:
                xx, yy = (x, y+i) if vertical else (x+i, y)
                if 0 <= xx < 32 and 0 <= yy < 32:
                    total += image[yy][xx]*w
            row.append(total*reciprocal//(512*65536) if 'reciprocal16' in model else total//denom)
        output.append(row)
    return output


def analyze(native):
    cases = decode(native)
    scores = {name: {'exact': 0, 'samples': 0, 'failures': []} for name in MODELS}
    input_exact = 0
    for case in cases:
        i, k, alpha, pattern, axis, bx, by = case['key']
        image = source(int(alpha), int(pattern))
        for x, pixel in enumerate(case['input']):
            assert pixel == [image[16][x]]*4, (i, x, pixel, image[16][x])
            input_exact += 1
        for name, score in scores.items():
            output = axis_pass(axis_pass(image, bx, False, name), by, True, name)[16]
            for x, (value, expected) in enumerate(zip(output, case['filtered'])):
                score['samples'] += 1
                if [value]*4 == expected:
                    score['exact'] += 1
                else:
                    score['failures'].append({'case': int(i), 'kernel': k, 'alpha': alpha,
                        'pattern': int(pattern), 'axis': int(axis), 'x': x, 'actual': value, 'native': expected})
    return {'input_exact': input_exact, 'models': scores, 'production_admitted': False,
            'scope': 'Explicit BlurFilter applyFilter; no implicit Glow or GPU implementation admission.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = analyze(args.native)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('input', result['input_exact'])
    print({k: (v['exact'], v['samples']) for k, v in result['models'].items()})
