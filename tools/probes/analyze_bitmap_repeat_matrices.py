#!/usr/bin/env python3
"""Measure repeat matrix routing and a signed-byte hypothesis; never admit production."""
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
from tools.probes.analyze_bitmap_sampling_r27 import analyze as clipped_regressions, events, rgb, ROOT
from tools.probes.bitmap_sampling_candidate import coordinates, interpolate


def identities():
    return [(corner, scale, route, period, fraction) for corner in range(4)
            for scale in (1.01, 1.7, 2.5, 5, 7.99, 8, 13.3) for route in range(3)
            for period in (-128, -1, 0, 1, 128) for fraction in (-.125, 0, .25, .5, .875, 1, 1.125)]


def signed_byte_coordinate(value):
    # This deliberately differs from floor at exact negative integer byte coordinates.
    # It is a diagnostic hypothesis constrained by native impulses, not a runtime fix.
    return (math.trunc(value*256) - (1 if value < 0 else 0))/256


def capture(text):
    return events(text, 'bitmap-repeat-matrices', identities(), lambda _: 1, 'matrix', revision='r28')


def analyze(root=ROOT):
    hashes = {}
    def read(path):
        data = (root/path).read_bytes()
        hashes[path] = hashlib.sha256(data).hexdigest()
        return data.decode()
    native = capture(read('r28/matrices/native.log'))
    groups = defaultdict(list)
    binary_controls = []
    constant = 0
    for identity, pixels in native:
        corner, scale, route, period, fraction = identity
        value = rgb(pixels[0])
        constant += value[2] == 113
        groups[corner, scale, route, fraction].append({'period': period, 'rgb': value})
        # Only these controls have exact binary scale, quarter draw translation and
        # integer fill translation. Fractional fill composition is separately unresolved.
        if scale != 8 or route == 2:
            continue
        tx = 32.5-(fraction+.5)*scale-2*period*scale
        ty = 32.5-.85*scale
        x, y = coordinates(scale, tx, ty, 32, 32)
        def texel(a, b):
            return (255*int((b % 2)*2+a % 2 == corner), (b % 2)*255, 113)
        before = interpolate(x, y, texel, byte_weights=True)
        after = interpolate(signed_byte_coordinate(x), signed_byte_coordinate(y), texel, byte_weights=True)
        binary_controls.append({'identity': identity, 'native_rgb': value,
                                'floor_rgb': before, 'signed_rgb': after})
    period_controls = [{'identity': key, 'observations': values,
                        'exact': len({tuple(v['rgb']) for v in values}) == 1}
                       for key, values in groups.items()]
    scores, failures = [], []
    for kind, path in (('scalar-repeat', 'r24/scalar-repeat/native.log'), ('repeat', 'r23/inverse/native.log')):
        rows = inverse_capture(read(path), kind)['rows']
        count = before_count = 0
        max_delta = 0
        for r in rows:
            x, y = coordinates(r['scale'], r['phase']/256, -r['phase']/512, r['x'], r['y'])
            def texel(a, b):
                return [r['alpha']*v for v in COLORS[b % 2][a % 2]]
            byte = kind == 'scalar-repeat'
            before = interpolate(x, y, texel, byte_weights=byte)
            after = interpolate(signed_byte_coordinate(x), signed_byte_coordinate(y), texel, byte_weights=byte)
            before_count += before == r['native_rgb']
            count += after == r['native_rgb']
            delta = max(abs(a-b) for a, b in zip(after, r['native_rgb']))
            max_delta = max(max_delta, delta)
            if delta:
                failures.append({'suite': kind, 'scale': r['scale'], 'phase': r['phase'],
                                 'x': r['x'], 'y': r['y'], 'alpha': r['alpha'],
                                 'native_rgb': r['native_rgb'], 'candidate_rgb': after, 'max_delta': delta})
        scores.append({'suite': kind, 'samples': len(rows), 'before_exact': before_count,
                       'exact': count, 'max_delta': max_delta})
    clipped = clipped_regressions(root)
    regressions = [s for s in clipped['scores'] if s['suite'] not in ('repeat', 'scalar-repeat')]
    return {'production_admitted': False,
            'passed': all(s['exact'] == s['samples'] for s in scores+regressions),
            'native_samples': len(native), 'constant_channel_exact': constant,
            'period_controls': period_controls,
            'period_control_summary': [{'route': route, 'groups': 196,
                                        'different': sum(not c['exact'] for c in period_controls
                                                         if c['identity'][2] == route)} for route in range(3)],
            'binary_controls': binary_controls,
            'binary_control_summary': {'samples': len(binary_controls),
                                      'floor_exact': sum(r['native_rgb'] == r['floor_rgb'] for r in binary_controls),
                                      'signed_exact': sum(r['native_rgb'] == r['signed_rgb'] for r in binary_controls)},
            'repeat_scores': scores, 'clipped_regressions': regressions,
            'reference_sha256': {**clipped['reference_sha256'], **hashes}, 'failures': failures}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('passed', 'production_admitted', 'native_samples',
                                           'period_control_summary', 'binary_control_summary', 'repeat_scores')}))
    raise SystemExit(0 if report['passed'] else 1)
