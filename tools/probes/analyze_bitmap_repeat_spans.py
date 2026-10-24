#!/usr/bin/env python3
"""Validate geometric repeat spans against native impulses; CPU diagnostics only."""
import argparse
from collections import defaultdict, Counter
import hashlib
import json
import math
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.probes.analyze_bitmap_inverse import analyze as inverse_capture, COLORS
from tools.probes.analyze_bitmap_repeat_rounding import coordinate, capture as old_capture, unique_texel, analyze as scalar_regressions
from tools.probes.analyze_bitmap_sampling_r27 import events, boundary_identities, rgb, ROOT
from tools.probes.bitmap_repeat_span_candidate import span_modes, sample


def capture(text, kind):
    lengths = (1, 3, *range(4, 17)) if kind == 'interval' else (255, 256, 257, 513)
    starts = range(2, 9) if kind == 'interval' else (3, 5)
    identities = [(pattern, case, start, length) for pattern in range(6)
                  for case in range(2) for start in starts for length in lengths]
    name = 'intervals' if kind == 'interval' else 'chunks'
    return events(text, 'bitmap-repeat-span-'+name, identities, lambda i: i[-1], kind, revision='r31')


def impulse(pattern):
    return lambda x, y: [255*int((y % 2*2+x % 2 == pattern) if pattern < 4
                                else (x if pattern == 4 else y) % 2), 113, 113]


def signature(qx, qy, mode):
    """All four red impulses and independent X/Y ramps over one two-texel period."""
    return tuple(sample(qx/256, qy/256, impulse(p), mode)[0] for p in range(6))


def recover_intervals(groups):
    observed = {tuple(values[p] for p in range(6)) for values in groups.values()}
    # The unchanged scalar initializer gives y=16/256. Independently invert all
    # possible byte coordinates for both axes, retaining every compatible result.
    # Ramp values restrict the search before corner signatures are evaluated.
    candidates = {sig: defaultdict(list) for sig in observed}
    ramp_pairs = {(sig[4], sig[5]) for sig in observed}
    for qx in range(512):
        fx, ix = qx % 256, qx//256
        wx = fx if ix == 0 else 256-fx
        for qy in range(512):
            fy, iy = qy % 256, qy//256
            wy = fy if iy == 0 else 256-fy
            # Separable ramps are exact one-axis interpolations. Byte-weight
            # residuals can change a ramp by one, so do not prune that neighbor.
            if not any((a, b) in ramp_pairs for a in (wx*255//256-1, wx*255//256, wx*255//256+1)
                       for b in (wy*255//256-1, wy*255//256, wy*255//256+1)):
                continue
            for mode in ('byte', 'vertical', 'horizontal'):
                sig = signature(qx, qy, mode)
                if sig in candidates:
                    candidates[sig][mode].append([qx, qy])
    recovered, family_counts = [], Counter()
    for key, values in groups.items():
        sig = tuple(values[p] for p in range(6))
        matches = dict(candidates[sig])
        family_counts[','.join(sorted(matches))] += 1
        case, start, length, offset = key
        x = coordinate((5, 3)[case], -(0, -15)[case], start+offset, 2)
        y = coordinate(8, 0, 4, 2)
        fixed_matches = [mode for mode in ('byte', 'vertical', 'horizontal')
                         if signature(int(x*256) % 512, int(y*256) % 512, mode) == sig]
        recovered.append({'identity': key, 'native_red_responses': sig,
                          'compatible_byte_coordinates_modulo_2': matches,
                          'fixed_scalar_compatible_modes': fixed_matches})
    return {'groups': len(groups), 'all_explained_without_coordinate_change': all(
                row['fixed_scalar_compatible_modes'] for row in recovered),
            'interval_convention': 'Each [qx,qy] denotes [q/256,(q+1)/256) per axis, modulo2; ambiguity retained.',
            'family_counts': dict(family_counts), 'rows': recovered}


def analyze(root=ROOT):
    scores, failures, hashes = [], [], {}
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
    groups, run_inventory = defaultdict(dict), []
    for kind, folder in [('interval', 'intervals'), ('chunk', 'chunks')]:
        rows = []
        for identity, pixels in capture(read(f'r31/{folder}/native.log'), kind):
            pattern, case, start, length = identity
            scale, origin = (5, 3)[case], (0, -15)[case]
            y = coordinate(8, 0, 4, 2)
            xs, modes, runs = span_modes(scale, -origin, start, length, 2, y, 2)
            if pattern == 0:
                run_inventory.append({'suite': kind, 'case': case, 'start': start, 'length': length, 'runs': runs})
            for offset, pixel in enumerate(pixels):
                rows.append((identity+(offset,), rgb(pixel), sample(xs[offset], y, impulse(pattern), modes[offset])))
                if kind == 'interval':
                    groups[case, start, length, offset][pattern] = rgb(pixel)[0]
        score('r31_'+kind, rows)
    rows = []
    for identity, pixels in old_capture(read('r30/spans/native.log'), 'span'):
        size, corner, scale, origin, length = identity
        y = coordinate(8, 0, 4, size)
        xs, modes, _ = span_modes(scale, -origin, 4, length, size, y, size)
        for offset, pixel in enumerate(pixels):
            rows.append((identity+(offset,), rgb(pixel), sample(xs[offset], y, unique_texel(size, 0, corner), modes[offset])))
    score('r30_spans', rows)
    rows = []
    for r in inverse_capture(read('r23/inverse/native.log'), 'repeat')['rows']:
        scale, phase, x, y, alpha = (r[k] for k in ('scale', 'phase', 'x', 'y', 'alpha'))
        tx, ty = phase/256, -phase/512
        start = max(0, math.ceil(math.trunc(tx*4)/4))
        sy = coordinate(scale, ty, y, 2)
        xs, modes, _ = span_modes(scale, tx, start, 520-start, 2, sy, 2)
        texel = lambda a, b: [alpha*v for v in COLORS[b % 2][a % 2]]
        rows.append((r, r['native_rgb'], sample(xs[x-start], sy, texel, modes[x-start])))
    score('distant_repeat', rows)
    rows = []
    for identity, pixels in events(read('r27/boundary/native.log'), 'bitmap-boundary-spans',
                                    boundary_identities(), lambda i: i[-1], 'boundary'):
        mode, size, corner, scale, side, delta, length = identity
        if mode != 1:
            continue
        tx = 32.5-((0 if side == 0 else size-1)+.5)*scale
        left, y = 32+delta, coordinate(scale, .25, 4, 2)
        xs, modes, _ = span_modes(scale, tx, left, length, size, y, 2)
        def texel(a, b):
            a, b = a % size, b % 2
            return [255*int(a == (size-1 if corner % 2 == 0 else 0) and b == corner//2),
                    17 if a == 0 else 223 if a == size-1 else 61, 113]
        for offset, pixel in enumerate(pixels):
            rows.append((identity+(offset,), rgb(pixel), sample(xs[offset], y, texel, modes[offset])))
    score('r27_repeat_boundaries', rows)
    old = scalar_regressions(root)
    scalar_names = {'r29_coefficient', 'r29_step', 'scalar-repeat', 'r29_negative', 'r28_binary_routes',
                    'rounding_even_half_and_period', 'half_even_half_and_period', 'spans_scalar_lengths_1_3'}
    regressions = [row for row in old['scores'] if row['suite'] in scalar_names]+old['clipped_regressions']
    hashes.update(old['reference_sha256'])
    intervals = recover_intervals(groups)
    passed = (all(row['exact'] == row['samples'] for row in scores+regressions)
              and intervals['all_explained_without_coordinate_change'])
    return {'arithmetic_passed': passed, 'production_admitted': False,
            'production_status': 'CPU model only; renderer binding and GPU/native parity not implemented or verified.',
            'scores': scores, 'regressions': regressions, 'failures': failures,
            'coordinate_intervals': intervals, 'geometric_runs': run_inventory,
            'reference_sha256': hashes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('arithmetic_passed', 'production_admitted', 'scores')}))
    raise SystemExit(0 if report['arithmetic_passed'] else 1)
