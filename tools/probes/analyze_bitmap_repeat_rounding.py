#!/usr/bin/env python3
"""Check repeat scalar rounding and reject unproven continuous-span admission."""
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
from tools.probes.analyze_bitmap_repeat_coefficients import capture as old_capture, texel, analyze as previous
from tools.probes.analyze_bitmap_repeat_matrices import capture as matrix_capture
from tools.probes.analyze_bitmap_sampling_r27 import events, rgb, ROOT
from tools.probes.bitmap_sampling_candidate import interpolate


def coordinate(scale, translation, pixel, size, *, half_even=True, denominator_minus_one=True):
    """Diagnostic scalar model; positive axis scales and identity fill matrix only."""
    if scale <= 0 or size < 1 or int(size) != size:
        raise ValueError('Expected positive scale and integer bitmap size')
    inverse = math.floor(65536/scale+.5)
    half = round(inverse/2) if half_even else math.floor(inverse/2+.5)
    translation = math.trunc(translation*4)/4
    fixed = pixel*inverse+math.floor(-translation/scale*65536+.5)+half-32768
    # Keep normalization rational: the new N=2 controls distinguish this from
    # 1+1/(N*65536). No floating epsilon should decide a byte-grid boundary.
    if denominator_minus_one:
        numerator, denominator = fixed*size*256, size*65536-1
    else:
        numerator, denominator = fixed*(size*65536+1)*256, size*65536*65536
    byte = abs(numerator)//denominator
    if numerator < 0:
        byte = -byte-1
    return byte/256


def capture(text, kind):
    if kind == 'rounding':
        identities = [(n, a, c, o, p) for n in (2, 4, 8, 16) for a in range(2)
                      for c in range(4) for o in (14, 15, 16) for p in (3, 4, 5)]
        name, count = 'rounding', lambda _: 1
    elif kind == 'half':
        identities = [(n, s, a, c, o, p) for n in (2, 4, 8, 16) for a in range(2)
                      for c in range(4) for s in (3, 5, 7, 11, 13, 1.7)
                      for o in (0, 3, 7, 14, 15, 16, 31) for p in (3, 4, 5)]
        name, count = 'half-step', lambda _: 1
    elif kind == 'span':
        identities = [(n, c, s, o, length) for n in (2, 4, 8, 16) for c in range(4)
                      for s in (3, 5, 8, 1.7) for o in (-15, 0, 15) for length in (1, 3, 4, 5, 7, 8)]
        name, count = 'short-spans', lambda identity: identity[-1]
    else:
        raise ValueError('Unknown r30 capture kind')
    return events(text, 'bitmap-repeat-'+name, identities, count, kind, revision='r30')


def unique_texel(size, axis, corner):
    return lambda x, y: [255*int(y % 2*2+x % 2 == corner),
                         (((x if axis == 0 else y) % size)*37+17) % 256, 113]


def analyze(root=ROOT):
    hashes, scores, failures = {}, [], []
    def read(path):
        data = (root/path).read_bytes()
        hashes[path] = hashlib.sha256(data).hexdigest()
        return data.decode()
    def score(name, rows, *, retain_failures=True):
        bad = [{'suite': name, 'identity': identity, 'native_rgb': native, 'candidate_rgb': predicted,
                'max_delta': max(abs(a-b) for a, b in zip(native, predicted))}
               for identity, native, predicted in rows if native != predicted]
        scores.append({'suite': name, 'samples': len(rows), 'exact': len(rows)-len(bad),
                       'max_delta': max((r['max_delta'] for r in bad), default=0)})
        if retain_failures:
            failures.extend(bad)
    def axes(axis, variable, other):
        return (variable, other) if axis == 0 else (other, variable)
    for kind, folder in [('coefficient', 'coefficients'), ('step', 'step')]:
        rows = []
        for identity, pixels in old_capture(read(f'r29/{folder}/native.log'), kind):
            axis, corner, scale, origin = identity
            variable = coordinate(scale, -origin if kind == 'coefficient' else 0,
                                  4 if kind == 'coefficient' else 4+origin, 4)
            xy = axes(axis, variable, coordinate(8, 0, 4, 4))
            rows.append((identity, rgb(pixels[0]), interpolate(*xy, texel(axis, corner), byte_weights=True)))
        score('r29_'+kind, rows)
    for kind, path in [('scalar-repeat', 'r24/scalar-repeat/native.log'), ('repeat', 'r23/inverse/native.log')]:
        rows = []
        for r in inverse_capture(read(path), kind)['rows']:
            x = coordinate(r['scale'], r['phase']/256, r['x'], 2)
            y = coordinate(r['scale'], -r['phase']/512, r['y'], 2)
            sample = lambda a, b: [r['alpha']*v for v in COLORS[b % 2][a % 2]]
            rows.append((r, r['native_rgb'], interpolate(x, y, sample, byte_weights=kind == 'scalar-repeat')))
        score(kind, rows)
    rows = []
    for identity, pixels in old_capture(read('r29/negative/native.log'), 'negative'):
        axis, corner, base, delta = identity
        xy = axes(axis, coordinate(8+delta/4096, 4.5-(base+.5)*8, 4, 2), coordinate(8, 0, 4, 2))
        sample = lambda a, b: [255*int(b % 2*2+a % 2 == corner), b % 2*255, 113]
        rows.append((identity, rgb(pixels[0]), interpolate(*xy, sample, byte_weights=True)))
    score('r29_negative', rows)
    rows = []
    for identity, pixels in matrix_capture(read('r28/matrices/native.log')):
        corner, scale, route, period, fraction = identity
        if scale != 8 or route == 2:
            continue
        tx, ty = 32.5-(fraction+.5)*scale-2*period*scale, 32.5-.85*scale
        sample = lambda a, b: [255*int(b % 2*2+a % 2 == corner), b % 2*255, 113]
        xy = coordinate(scale, tx, 32, 2), coordinate(scale, ty, 32, 2)
        rows.append((identity, rgb(pixels[0]), interpolate(*xy, sample, byte_weights=True)))
    score('r28_binary_routes', rows)
    for kind in ('rounding', 'half'):
        native = capture(read(f'r30/{kind}/native.log'), kind)
        for variant, even, denominator in [('r29', False, False), ('even_half_only', True, False),
                                            ('even_half_and_period', True, True)]:
            rows = []
            for identity, pixels in native:
                if kind == 'rounding':
                    size, axis, corner, origin, pixel = identity
                    scale = 3
                else:
                    size, scale, axis, corner, origin, pixel = identity
                kwargs = {'half_even': even, 'denominator_minus_one': denominator}
                xy = axes(axis, coordinate(scale, -origin, pixel, size, **kwargs),
                          coordinate(8, 0, 4, size, **kwargs))
                rows.append((identity, rgb(pixels[0]), interpolate(*xy, unique_texel(size, axis, corner), byte_weights=True)))
            score(kind+'_'+variant, rows)
    spans = capture(read('r30/spans/native.log'), 'span')
    groups = defaultdict(dict)
    for identity, pixels in spans:
        size, corner, scale, origin, length = identity
        groups[size, corner, scale, origin][length] = pixels
    # Fixed whole-suite hypotheses only; never choose arithmetic by native RGB.
    for mode in ('byte', 'separable', 'groups4'):
        rows = []
        for identity, pixels in spans:
            size, corner, scale, origin, length = identity
            for offset, pixel in enumerate(pixels):
                x, y = coordinate(scale, -origin, 4+offset, size), coordinate(8, 0, 4, size)
                byte = mode == 'byte' or (mode == 'groups4' and offset >= length//4*4)
                predicted = interpolate(x, y, unique_texel(size, 0, corner), byte_weights=byte)
                rows.append((identity+(offset,), rgb(pixel), predicted))
        score('spans_'+mode, rows, retain_failures=mode == 'groups4')
        if mode == 'byte':
            score('spans_scalar_lengths_1_3', [r for r in rows if r[0][-2] <= 3])
    overlaps = []
    for first, second in ((1, 3), (1, 4), (3, 4), (4, 5), (4, 7), (4, 8), (5, 7), (5, 8), (7, 8)):
        differences = [{'identity': key, 'offset': offset, 'short_rgb': rgb(values[first][offset]),
                        'long_rgb': rgb(values[second][offset])}
                       for key, values in groups.items() for offset in range(first)
                       if values[first][offset] != values[second][offset]]
        overlaps.append({'lengths': [first, second], 'samples': len(groups)*first,
                         'different': len(differences), 'differences': differences})
    old = previous(root)
    hashes.update(old['reference_sha256'])
    return {'production_admitted': False, 'passed': False, 'scores': scores, 'failures': failures,
            'span_overlap_controls': overlaps, 'clipped_regressions': old['clipped_regressions'],
            'reference_sha256': hashes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'scores': report['scores'], 'production_admitted': False}))
    raise SystemExit(1)
