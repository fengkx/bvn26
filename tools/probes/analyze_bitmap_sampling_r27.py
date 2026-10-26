#!/usr/bin/env python3
"""Check the r27 initializer/clipped-span hypothesis against independent natives."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.probes import analyze_bitmap_inverse as inverse
from tools.probes import analyze_bitmap_phase as phase
from tools.probes import analyze_bitmap_spans as spans
from tools.probes import analyze_bitmap_axis_ramps as axes
from tools.probes.bitmap_sampling_candidate import coordinates, interpolate, sample_clipped

ROOT = Path(__file__).resolve().parents[2] / 'evidence/importer-loud-fail'


def events(text, name, identities, count, kind, *, revision='r27'):
    parsed = [line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    if (len(parsed) != len(identities)+1 or any(len(e) != 8 for e in parsed)
            or len({e[1] for e in parsed}) != 1
            or not parsed[0][1].startswith(f'filter-{name}-{revision}-')
            or [int(e[2]) for e in parsed] != list(range(len(parsed)))
            or parsed[-1][6:] != ['done', 'ok']):
        raise ValueError('Incomplete, mixed or duplicate r27 capture')
    rows = []
    for event, identity in zip(parsed, identities):
        values = event[7].split(',')
        if (event[6] != kind or len(values) != len(identity)+count(identity)
                or tuple(map(float, values[:len(identity)])) != identity):
            raise ValueError('r27 identity/sample count mismatch')
        pixels = list(map(int, values[len(identity):]))
        if any(not 0 <= p <= 0xffffff for p in pixels):
            raise ValueError('Invalid native RGB pixel')
        rows.append((identity, pixels))
    return rows


def boundary_identities():
    return [(mode, size, corner, scale, side, delta, length)
            for mode in (0, 1) for size in (4, 8, 16) for corner in range(4)
            for scale in (5, 8) for side in (0, 1) for delta in range(-3, 4) for length in (1, 5)]


def origin_identities():
    return [(corner, scale, origin, shift) for corner in range(4) for scale in (2.5, 5, 8)
            for origin in (4, 5, 8, 17, 63, 127, 255, 511) for shift in range(-8, 9)]


def rgb(pixel):
    return [(pixel >> shift) & 255 for shift in (16, 8, 0)]


def analyze(root=ROOT):
    hashes, scores, failures = {}, [], []
    def read(path):
        data = (root/path).read_bytes()
        hashes[path] = hashlib.sha256(data).hexdigest()
        return data.decode()
    def score(name, rows):
        differences = []
        for identity, native, predicted in rows:
            if native != predicted:
                differences.append({'suite': name, 'identity': identity, 'native_rgb': native,
                                    'candidate_rgb': predicted,
                                    'max_delta': max(abs(a-b) for a, b in zip(native, predicted))})
        scores.append({'suite': name, 'samples': len(rows), 'exact': len(rows)-len(differences),
                       'max_delta': max((r['max_delta'] for r in differences), default=0)})
        failures.extend(differences)
    def basis(alpha):
        return lambda x, y: [alpha*v for v in inverse.COLORS[y % 2][x % 2]]
    for extended, folder in ((False, 'bitmap-phase'), (True, 'bitmap-phase-extended')):
        text = read(f'r22/{folder}/native.log')
        phase.analyze(text, extended=extended)  # Strict legacy capture validation.
        rows = []
        for line in text.splitlines():
            e = line.split('|')
            if len(e) != 8 or e[6] != 'phase':
                continue
            values = list(map(int, e[7].split(','))) if not extended else list(map(float, e[7].split(',')))
            alpha, scale = values[:2]
            for p, pixel in zip(range(-256 if extended else 0, 256), values[2:]):
                tx, ty = p/256, -p/512 if extended else 0
                predicted = interpolate(*coordinates(scale, tx, ty, math.floor(scale), math.floor(scale)),
                                        basis(alpha), byte_weights=True)
                rows.append(((alpha, scale, p), rgb(int(pixel)), predicted))
        score(folder, rows)
    for kind, path in (('clipped', 'r23/inverse-clipped'), ('row', 'r23/row'),
                       ('scalar-clipped', 'r24/scalar-clipped'), ('repeat', 'r23/inverse'),
                       ('scalar-repeat', 'r24/scalar-repeat')):
        parsed = inverse.analyze(read(path+'/native.log'), kind)
        rows = []
        for r in parsed['rows']:
            scale, p, x, y, alpha = (r[k] for k in ('scale', 'phase', 'x', 'y', 'alpha'))
            tx, ty = p/256, -p/512
            if 'repeat' in kind:
                # Initializer-only control; this does not claim a repeat span partition.
                predicted = interpolate(*coordinates(scale, tx, ty, x, y), basis(alpha),
                                        byte_weights=kind.startswith('scalar'))
            else:
                scalar = kind.startswith('scalar')
                predicted = sample_clipped(scale, tx, ty, x, y, basis(alpha),
                                           clip_left=x if scalar else 0, clip_right=x+1 if scalar else 520,
                                           source_width=1024, source_height=1024)
            rows.append(((scale, p, x, y, alpha), r['native_rgb'], predicted))
        score(kind, rows)
    text = read('r24/spans/native.log')
    spans.analyze(text)
    rows, excluded = [], 0
    for line in text.splitlines():
        e = line.split('|')
        if len(e) != 8 or e[6] != 'span':
            continue
        v = list(map(float, e[7].split(',')))
        mode, width, left, scale, p = v[:5]
        if mode:
            continue
        for x, pixel in enumerate(v[5:], 16):
            if x < left:
                excluded += 1
                continue
            predicted = sample_clipped(scale, p/256, -p/512, x, 155, basis(255),
                                       clip_left=int(left), clip_right=int(width),
                                       source_width=1024, source_height=1024)
            rows.append(((width, left, scale, p, x), rgb(int(pixel)), predicted))
    score('independent_clipped_widths', rows)
    parsed = axes.analyze(read('r26/axis/native.log'))
    rows = []
    for r in parsed['rows']:
        mode, scale, tx, ty, left, length = r['identity']
        if mode % 2:
            continue
        size = 1024 if mode == 0 else 4
        predicted = sample_clipped(scale, tx, ty, r['x'], 4, lambda x, y: axes.texel(mode, x, y),
                                   clip_left=left, clip_right=left+length, source_width=size,
                                   source_height=size, shape_left=-32)
        rows.append(((*r['identity'], r['offset']), r['native_rgb'], predicted))
    score('independent_clipped_axes', rows)
    origin = events(read('r27/origin/native.log'), 'bitmap-origin-sweep', origin_identities(),
                    lambda _: 1, 'origin')
    rows, origin_groups = [], defaultdict(list)
    for identity, pixels in origin:
        corner, scale, x, shift = identity
        tx = x-4+shift/8
        def texel(a, b):
            return (255*int((b*2+a % 2) == corner), b*255, 113)
        predicted = sample_clipped(scale, tx, .25, x, 4, texel, clip_left=x, clip_right=x+1,
                                   source_width=1024, source_height=2, shape_left=-1024)
        rows.append((identity, rgb(pixels[0]), predicted))
        if shift % 2 == 0:  # Exact quarter phases avoid a sign/truncation confound.
            origin_groups[corner, scale, shift].append({'origin': x, 'rgb': rgb(pixels[0])})
    score('independent_origin_sweep', rows)
    boundary = events(read('r27/boundary/native.log'), 'bitmap-boundary-spans', boundary_identities(),
                      lambda i: i[-1], 'boundary')
    rows, widths, singles, observations = [], defaultdict(list), {}, []
    for identity, pixels in boundary:
        mode, size, corner, scale, side, delta, length = identity
        tx = 32.5-((0 if side == 0 else size-1)+.5)*scale
        left = 32+delta
        def texel(a, b):
            return (255*int(a == (size-1 if corner % 2 == 0 else 0) and b == corner//2),
                    17 if a == 0 else 223 if a == size-1 else 61, 113)
        for offset, pixel in enumerate(pixels):
            native = rgb(pixel)
            key = (mode, size, corner, scale, side, delta+offset)
            if length == 1:
                singles[key] = native
            observations.append((key, identity, offset, native))
            widths[mode, corner, scale, side, delta, length, offset].append(native)
            if mode == 0:
                predicted = sample_clipped(scale, tx, .25, left+offset, 4, texel,
                                           clip_left=left, clip_right=left+length, source_width=size,
                                           source_height=2, shape_left=-128)
                rows.append(((*identity, offset), native, predicted))
    score('independent_clipped_boundaries', rows)
    boundary_differences = []
    counts = {0: [0, 0], 1: [0, 0]}
    for key, identity, offset, native in observations:
        if identity[-1] != 5 or key not in singles:
            continue
        counts[key[0]][0] += 1
        if native != singles[key]:
            counts[key[0]][1] += 1
            boundary_differences.append({'identity': identity, 'offset': offset,
                                         'single_rgb': singles[key], 'span_rgb': native})
    return {'production_admitted': False, 'passed': all(s['exact'] == s['samples'] for s in scores),
            'scores': scores, 'reference_sha256': hashes, 'failures': failures,
            'outside_clip_observations_excluded': excluded,
            'quarter_origin_controls': [{'identity': k, 'observations': v,
                                         'exact': len({tuple(r['rgb']) for r in v}) == 1}
                                        for k, v in origin_groups.items()],
            'width_controls': len(widths),
            'width_controls_exact': sum(len({tuple(v) for v in group}) == 1 for group in widths.values()),
            'boundary_single_vs_span_counts': counts, 'boundary_context_differences': boundary_differences}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze()
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('passed', 'production_admitted', 'scores',
                                           'width_controls', 'width_controls_exact',
                                           'boundary_single_vs_span_counts')}))
    raise SystemExit(0 if result['passed'] else 1)
