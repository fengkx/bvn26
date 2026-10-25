"""Intersect integer-fill phase controls with independently measured old bounds."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path

from tools.probes.analyze_affine_fill_phase import analyze as old_phase
from tools.probes.analyze_affine_scale_split import property_float32
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_nearest_affine import inverse
from tools.probes.run_nested_filters import unpack


def analyze(native, old_native):
    records = events(native)
    assert len(records) == 3887
    source, samples = [], []
    for kind, payload in records:
        v = payload.split(',')
        if kind == 'source':
            assert int(v[0]) == len(source) // 16 and len(v) == 33
            source.extend(unpack(list(map(int, v[1:]))))
        elif kind == 'sample':
            assert len(v) == 27 and int(v[0]) == len(samples)
            samples.append((v[:25], unpack(list(map(int, v[25:])))[0]))
        else:
            assert [kind, payload] == ['done', 'ok']
    assert source == [[x, y, 73, 255] for y in range(16) for x in range(16)]
    old = old_phase(old_native)
    old_groups = {(v['phase'], v['axis'], v['position']): v for v in old['groups']}
    old_zero = {}
    for kind, payload in events(old_native):
        if kind == 'sample':
            v = payload.split(',')
            if v[3] == '0':
                old_zero[tuple(map(int, (v[1], v[2], v[4])))] = (v[21:23], unpack(list(map(int, v[23:])))[0])
    groups, scores = {}, {}
    zero_exact = zero_samples = 0
    for k, pixel in samples:
        phase, axis, step, position = map(int, k[1:5])
        assert list(map(Fraction, k[23:25])) == [64, 64]
        assert list(map(Fraction, k[17:19])) == ([step, 0] if axis == 0 else [0, step])
        cm = list(map(property_float32, k[5:11]))
        assert cm[4:] == [0, 0]
        effective = k[:17]
        effective[5:9] = [str(v * 64) for v in cm[:4]]
        co = inverse(effective)
        x, y = map(int, k[21:23])
        delta = Fraction(step, 64)
        assert pixel[2:] == [73, 255] and all(0 <= v < 16 for v in pixel[:2])
        assert all(1 <= a * xx + b * yy + t - (delta if i == axis else 0) <= 15
                   for i, (a, b, t) in enumerate(co)
                   for xx, yy in ((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)))
        key = phase, axis, position
        if step == 0:
            zero_samples += 1
            zero_exact += old_zero[key] == (k[21:23], pixel)
        groups.setdefault(key, []).append({'step': step, 'pixel': pixel})
        fixed = [[math.floor(v * 65536 + Fraction(1, 2)) for v in row] for row in co]
        paths = {
            'exact_center': [a * (x + Fraction(1, 2)) + b * (y + Fraction(1, 2)) + t for a, b, t in co],
            'fixed_center': [Fraction(a * x + b * y + t + round(Fraction(a + b, 2)), 65536) for a, b, t in fixed],
        }
        for name, values in paths.items():
            result = [math.floor(q - (delta if i == axis else 0)) for i, q in enumerate(values)] + [73, 255]
            r = scores.setdefault(f'phase{phase}/{name}', {'samples': 0, 'exact': 0, 'max_channel_delta': 0, 'failures': []})
            r['samples'] += 1
            r['exact'] += result == pixel
            r['max_channel_delta'] = max(r['max_channel_delta'], max(abs(a - b) for a, b in zip(result, pixel)))
            if result != pixel:
                r['failures'].append({'key': k, 'actual': result, 'native': pixel})
    rows = []
    for key, values in groups.items():
        assert [v['step'] for v in values] == list(range(-64, 65))
        phase, axis, position = key
        lower = max(values, key=lambda v: Fraction(v['pixel'][axis]) + Fraction(v['step'], 64))
        upper = min(values, key=lambda v: Fraction(v['pixel'][axis]) + Fraction(v['step'], 64) + 1)
        lo = Fraction(lower['pixel'][axis]) + Fraction(lower['step'], 64)
        hi = Fraction(upper['pixel'][axis]) + Fraction(upper['step'], 64) + 1
        old_row = old_groups[key]
        joint_lo = max(lo, Fraction(old_row['consumed_linear_lower']))
        joint_hi = min(hi, Fraction(old_row['consumed_linear_upper']))
        rows.append({'phase': phase, 'axis': axis, 'position': position,
                     'lower': str(lo), 'upper': str(hi), 'feasible': lo < hi,
                     'lower_witness': lower, 'upper_witness': upper,
                     'joint_lower': str(joint_lo), 'joint_upper': str(joint_hi),
                     'joint_feasible': joint_lo < joint_hi,
                     'other_channel_values': sorted({v['pixel'][1-axis] for v in values}),
                     'nonmonotone_steps': [b['step'] for a, b in zip(values, values[1:]) if b['pixel'][axis] > a['pixel'][axis]]})
    assert zero_samples == 30
    return {'source_texels_exact': 256, 'samples': len(samples),
            'old_zero_phase': {'samples': zero_samples, 'exact': zero_exact},
            'groups': rows, 'scores': scores,
            'affine_sampler_admitted': False, 'production_admitted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--old-native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    r = analyze(a.native, a.old_native)
    a.output.write_text(json.dumps(r, separators=(',', ':')) + '\n')
    print(r['old_zero_phase'])
    for k, v in r['scores'].items():
        print(k, v['exact'], v['samples'], v['max_channel_delta'])
    print('feasible', sum(v['feasible'] for v in r['groups']), 'joint', sum(v['joint_feasible'] for v in r['groups']))
