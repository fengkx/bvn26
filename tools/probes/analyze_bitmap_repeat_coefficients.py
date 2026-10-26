#!/usr/bin/env python3
"""Constrain repeat affine coefficients with independent native impulse captures."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.probes.analyze_bitmap_inverse import analyze as inverse_capture, COLORS
from tools.probes.analyze_bitmap_repeat_matrices import analyze as previous, signed_byte_coordinate
from tools.probes.analyze_bitmap_sampling_r27 import events, rgb, ROOT
from tools.probes.bitmap_sampling_candidate import coordinates, interpolate

SCALES = (1.01, 1.7, 2.5, 3, 5, 7.99, 8, 13.3, 1.3, 6.25)
ORIGINS = (0, 1, 3, 7, 15, 31, 63, 127, 255, 511, 1023, 2047, 4095, 8191, 16383)
EDGE = (17, 223, 61, 149)


def capture(text, kind):
    if kind == 'negative':
        identities = [(a, c, b, d) for a in range(2) for c in range(4)
                      for b in (-.5, -1, -1.5) for d in (-16, -4, -1, 0, 1, 4, 16)]
        name = 'negative-grid'
    else:
        origins = ORIGINS if kind == 'coefficient' else ORIGINS[:12]
        identities = [(a, c, s, o) for a in range(2) for c in range(4)
                      for s in SCALES for o in origins]
        name = 'coefficients' if kind == 'coefficient' else 'pixel-step'
    return events(text, 'bitmap-repeat-'+name, identities, lambda _: 1, kind, revision='r29')


def texel(axis, corner):
    return lambda x, y: [255*int(y % 2*2+x % 2 == corner), EDGE[(x if axis == 0 else y) % 4], 113]


def normalize(value, size):
    # Hypothesis from positive-origin intervals, not admitted runtime arithmetic.
    return signed_byte_coordinate(value*(1+1/(size*65536)))


def affine_intervals(rows):
    lookups = {}
    for axis in range(2):
        table = defaultdict(list)
        for q in range(1024):
            x, y = (q/256, 16/256) if axis == 0 else (16/256, q/256)
            signature = tuple(v for c in range(4) for v in
                              interpolate(x, y, texel(axis, c), byte_weights=True))
            table[signature].append(q)
        lookups[axis] = table
    groups = defaultdict(dict)
    for (axis, corner, scale, origin), pixels in rows:
        groups[axis, scale, origin][corner] = rgb(pixels[0])
    constraints, unresolved = defaultdict(list), []
    for (axis, scale, origin), values in groups.items():
        signature = tuple(v for c in range(4) for v in values[c])
        matches = lookups[axis][signature]
        if len(matches) != 1:
            unresolved.append({'identity': [axis, scale, origin], 'matches': matches})
            continue
        wrapped = matches[0]/256
        # RGB proves only modulo four. This explicitly assumes the nearest ideal period.
        ideal = (origin+4.5)/scale-.5
        lower = wrapped+4*round((ideal-wrapped)/4)
        constraints[axis, scale].append((origin, lower, lower+1/256))
    intervals = []
    for (axis, scale), points in constraints.items():
        lower, upper = -math.inf, math.inf
        for origin, lo, hi in points:
            for other, other_lo, other_hi in points:
                if other > origin:
                    lower = max(lower, (other_lo-hi)/(other-origin))
                    upper = min(upper, (other_hi-lo)/(other-origin))
        factor = 1+1/262144
        intervals.append({'axis': axis, 'scale': scale, 'held_out_scale': scale in (1.3, 6.25),
                          'slope_open_interval': [lower, upper], 'feasible': lower < upper,
                          'normalized_inverse': factor/scale,
                          'normalized_fixed_step': math.floor(65536/scale+.5)/65536*factor,
                          'coordinate_half_open_intervals': points})
    return {'groups': len(groups), 'unresolved': unresolved, 'intervals': intervals,
            'period_assumption': 'nearest ideal source period; absolute period is not observed'}


def analyze(root=ROOT):
    hashes, scores, failures, intervals = {}, [], [], {}
    def read(path):
        data = (root/path).read_bytes()
        hashes[path] = hashlib.sha256(data).hexdigest()
        return data.decode()
    def score(name, rows):
        bad = [{'suite': name, 'identity': identity, 'native_rgb': native, 'candidate_rgb': predicted,
                'max_delta': max(abs(a-b) for a, b in zip(native, predicted))}
               for identity, native, predicted in rows if native != predicted]
        scores.append({'suite': name, 'samples': len(rows), 'exact': len(rows)-len(bad),
                       'max_delta': max((r['max_delta'] for r in bad), default=0)})
        failures.extend(bad)
    for kind, folder in [('coefficient', 'coefficients'), ('step', 'step')]:
        native = capture(read(f'r29/{folder}/native.log'), kind)
        intervals[kind] = affine_intervals(native)
        rows = []
        for identity, pixels in native:
            axis, corner, scale, origin = identity
            variable = coordinates(scale, -origin if kind == 'coefficient' else 0, 0,
                                   4 if kind == 'coefficient' else 4+origin, 4)[0]
            other = coordinates(8, 0, 0, 4, 4)[0]
            variable, other = normalize(variable, 4), normalize(other, 4)
            x, y = (variable, other) if axis == 0 else (other, variable)
            rows.append((identity, rgb(pixels[0]), interpolate(x, y, texel(axis, corner), byte_weights=True)))
        score(kind, rows)
    negative = capture(read('r29/negative/native.log'), 'negative')
    for hypothesis in ('floor', 'signed', 'negative_fixed_epsilon'):
        rows = []
        for identity, pixels in negative:
            axis, corner, base, delta = identity
            variable = coordinates(8+delta/4096, 4.5-(base+.5)*8, 0, 4, 4)[0]
            other = coordinates(8, 0, 0, 4, 4)[0]
            x, y = (variable, other) if axis == 0 else (other, variable)
            if hypothesis == 'signed':
                x, y = signed_byte_coordinate(x), signed_byte_coordinate(y)
            elif hypothesis == 'negative_fixed_epsilon':
                x, y = x-(1/65536 if x < 0 else 0), y-(1/65536 if y < 0 else 0)
            sample = lambda a, b: [255*int(b % 2*2+a % 2 == corner), b % 2*255, 113]
            rows.append((identity, rgb(pixels[0]), interpolate(x, y, sample, byte_weights=True)))
        score('negative_'+hypothesis, rows)
    for kind, path in [('scalar-repeat', 'r24/scalar-repeat/native.log'), ('repeat', 'r23/inverse/native.log')]:
        rows = []
        for r in inverse_capture(read(path), kind)['rows']:
            x, y = coordinates(r['scale'], r['phase']/256, -r['phase']/512, r['x'], r['y'])
            sample = lambda a, b: [r['alpha']*v for v in COLORS[b % 2][a % 2]]
            predicted = interpolate(normalize(x, 2), normalize(y, 2), sample, byte_weights=kind == 'scalar-repeat')
            rows.append((r, r['native_rgb'], predicted))
        score(kind, rows)
    old = previous(root)
    hashes.update(old['reference_sha256'])
    return {'production_admitted': False, 'passed': False, 'scores': scores, 'failures': failures,
            'affine_constraints': intervals, 'clipped_regressions': old['clipped_regressions'],
            'reference_sha256': hashes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'scores': report['scores'], 'production_admitted': False}))
    raise SystemExit(1)
