"""Test shared slope arithmetic after independently constrained vertex ordering."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_affine_mask_coverage import decode
from tools.probes.analyze_affine_scan_coverage import scan_coverage


def vertices(key):
    width, height = map(int, key[3:5])
    a, b, c, d, tx, ty = map(Fraction, key[5:11])
    dx, dy = map(Fraction, key[15:17])
    return [(Fraction(round(4 * (a*x+c*y)) + round(4*tx) + math.trunc(4*dx), 4),
             Fraction(round(4 * (b*x+d*y)) + round(4*ty) + math.trunc(4*dy), 4))
            for x, y in ((0, 0), (width, 0), (width, height), (0, height))]


def fixed_scan(points, left, top, width, height, bits, mode):
    """Initialize each top endpoint once; step a single fixed slope per edge."""
    quantize = {'floor': math.floor, 'even': round, 'trunc': math.trunc}[mode]
    fixed = [(int(x*4), int(y*4)) for x, y in points]
    assert all((Fraction(x, 4), Fraction(y, 4)) == p for (x, y), p in zip(fixed, points))
    edges = []
    for (ax, ay), (bx, by) in zip(fixed, fixed[1:] + fixed[:1]):
        if ay > by:
            ax, ay, bx, by = bx, by, ax, ay
        if ay != by:
            slope = quantize(Fraction(bx-ax, by-ay) * (1 << bits))
            edges.append((ax, ay, by, slope))
    counts = [0] * (width * height)
    for yy in range(top*4, (top+height)*4):
        xs = [((ax << bits) + (yy-ay)*slope + (1 << (bits-1))) // (1 << bits)
              for ax, ay, by, slope in edges if ay <= yy < by]
        assert len(xs) in (0, 2)
        if not xs:
            continue
        lo, hi = sorted(xs)
        for x in range(left, left+width):
            counts[(yy//4-top)*width+x-left] += max(0, min(4*x+4, hi)-max(4*x, lo))
    assert all(0 <= v <= 16 for v in counts)
    return counts


def analyze(native):
    scores = {}
    for case in decode(native):
        key = case['key']; left, top, width, height = map(int, key[17:21])
        points = vertices(key)
        candidates = {f'exact/{mode}': scan_coverage(points, left, top, width, height, 0, 0, mode)
                      for mode in ('half_up', 'even')}
        for bits in (8, 16, 24):
            for mode in ('floor', 'even', 'trunc'):
                candidates[f'fixed{bits}/{mode}'] = fixed_scan(points, left, top, width, height, bits, mode)
        for name, counts in candidates.items():
            score = scores.setdefault(name, {'samples': 0, 'exact': 0, 'max_channel_delta': 0, 'failures': []})
            for i, (count, pixel) in enumerate(zip(counts, case['pixels'])):
                actual = [v*count//16 for v in (144, 120, 8, 255)]
                score['samples'] += 1; score['exact'] += actual == pixel
                score['max_channel_delta'] = max(score['max_channel_delta'], max(abs(p-q) for p,q in zip(actual,pixel)))
                if actual != pixel:
                    score['failures'].append({'case': int(key[1]), 'kind': int(key[2]),
                        'x': left+i%width, 'y': top+i//width, 'actual': actual, 'native': pixel})
    return {'scores': scores, 'coverage_admitted': False, 'production_admitted': False,
            'routing': 'one vertex order and one slope construction globally; no native RGB inputs'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); result = analyze(args.native)
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    for name, score in result['scores'].items():
        print(name, score['exact'], score['samples'], score['max_channel_delta'])
