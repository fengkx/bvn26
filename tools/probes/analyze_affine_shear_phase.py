"""Measure axis-separated shear phase without fitting a rendering initializer."""
import argparse
from fractions import Fraction
import json
from pathlib import Path

from tools.probes.analyze_affine_scale_split import property_float32
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


SHEARS = [Fraction(v) for v in ('-1', '-.75', '-.5', '-.25', '-.125', '0', '.125', '.25', '.5', '.75', '1')]


def analyze(native, old_summary):
    source, cases, samples = [], [], []
    for kind, payload in events(native):
        v = payload.split(',')
        if kind == 'source':
            assert int(v[0]) == len(source) // 16 and len(v) == 33
            source.extend(unpack(list(map(int, v[1:]))))
        elif kind == 'case':
            assert len(v) == 15 and int(v[0]) == len(cases)
            cases.append({'key': v, 'pixels': []})
        elif kind == 'row':
            pixels = cases[-1]['pixels']
            assert int(v[0]) == 96 + len(pixels) // 64 and len(v) == 129
            pixels.extend(unpack(list(map(int, v[1:]))))
        elif kind == 'sample':
            assert len(v) == 19 and int(v[0]) == len(samples)
            samples.append((v[:17], unpack(list(map(int, v[17:])))[0]))
        else:
            assert [kind, payload] == ['done', 'ok']
    assert source == [[x, y, 73, 255] for y in range(16) for x in range(16)]
    assert len(cases) == 44 and len(samples) == 17028
    full, pairs = {}, []
    for case in cases:
        k, pixels = case['key'], case['pixels']
        phase, direction, factor = int(k[1]), int(k[2]), int(k[4])
        h = Fraction(k[3])
        assert phase == direction * 11 + SHEARS.index(h) and factor in (1, 64)
        cm = list(map(property_float32, k[5:11]))
        expected = [1, 0, h, 1] if direction == 0 else [1, h, 0, 1]
        assert [v * factor for v in cm[:4]] == expected and cm[4:] == [0, 0]
        x, y, w, height = map(int, k[11:])
        assert 96 <= x < x + w <= 160 and 96 <= y < y + height <= 160
        assert len(pixels) == 4096
        full[phase, factor] = pixels
        if factor == 64:
            base = full[phase, 1]
            pairs.append({'phase': phase, 'direction': direction, 'shear': str(h), 'samples': 4096,
                          'exact': sum(a == b for a, b in zip(pixels, base)),
                          'max_channel_delta': max(abs(a-b) for p, q in zip(pixels, base) for a, b in zip(p, q))})
    groups = {}
    zero_exact = zero_samples = 0
    for k, pixel in samples:
        phase, direction, axis, step, position = int(k[1]), int(k[2]), int(k[4]), int(k[5]), int(k[6])
        h = Fraction(k[3])
        assert phase == direction * 11 + SHEARS.index(h)
        cm = list(map(property_float32, k[7:13]))
        assert [v * 64 for v in cm[:4]] == ([1, 0, h, 1] if direction == 0 else [1, h, 0, 1])
        assert cm[4:] == [0, 0] and pixel[2:] == [73, 255] and all(0 <= v < 16 for v in pixel[:2])
        x, y = map(int, k[15:17])
        if step == 0:
            zero_samples += 1
            zero_exact += full[phase, 1][(y-96)*64+x-96] == pixel
        corner = [Fraction(x-128) - h*(y-128), Fraction(y-128)] if direction == 0 else [Fraction(x-128), Fraction(y-128)-h*(x-128)]
        groups.setdefault((phase, direction, h, axis, position, corner[axis]), []).append({'step': step, 'pixel': pixel})
    old = {(v['phase'], v['axis'], v['position']): v for v in json.loads(old_summary.read_text())['groups']}
    rows = []
    for (phase, direction, h, axis, position, corner), values in groups.items():
        assert [v['step'] for v in values] == list(range(-64, 65))
        lo = max(Fraction(v['pixel'][axis]) + Fraction(v['step'], 64) for v in values)
        hi = min(Fraction(v['pixel'][axis]) + Fraction(v['step'], 64) + 1 for v in values)
        old_phase = 0 if h == 0 else 3 if direction == 0 and h == Fraction(1, 2) else 4 if direction == 0 and h == Fraction(-1, 2) else None
        joint = None
        if old_phase is not None:
            previous = old[old_phase, axis, position]
            joint = max(lo, Fraction(previous['joint_lower'])) < min(hi, Fraction(previous['joint_upper']))
        rows.append({'phase': phase, 'direction': direction, 'shear': str(h), 'axis': axis, 'position': position,
                     'lower': str(lo), 'upper': str(hi), 'feasible': lo < hi,
                     'corner': str(corner), 'offset_lower': str(lo-corner), 'offset_upper': str(hi-corner),
                     'old_joint_feasible': joint,
                     'other_channel_values': sorted({v['pixel'][1-axis] for v in values}),
                     'nonmonotone_steps': [b['step'] for a,b in zip(values,values[1:]) if b['pixel'][axis] > a['pixel'][axis]]})
    return {'source_texels_exact': 256, 'samples': len(samples), 'zero_phase_pairs': pairs,
            'zero_phase_scalar': {'samples': zero_samples, 'exact': zero_exact}, 'groups': rows,
            'affine_sampler_admitted': False, 'production_admitted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--old-summary', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    r = analyze(a.native, a.old_summary)
    a.output.write_text(json.dumps(r, indent=2)+'\n')
    print('zero full', sum(v['exact'] for v in r['zero_phase_pairs']), sum(v['samples'] for v in r['zero_phase_pairs']))
    print('zero scalar', r['zero_phase_scalar'])
    print('feasible', sum(v['feasible'] for v in r['groups']), len(r['groups']))
    print('old joint', sum(v['old_joint_feasible'] is True for v in r['groups']), sum(v['old_joint_feasible'] is not None for v in r['groups']))
