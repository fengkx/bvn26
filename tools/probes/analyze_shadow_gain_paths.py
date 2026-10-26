"""Constrain gain quantization with native byte ramps on both filter APIs."""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
from tools.probes.analyze_blur_kernel_heldout import ROOT
from tools.probes.run_nested_filters import unpack

MODELS = ('continuous_gain', 'byte_gain_floor', 'byte_gain_nearest', 'premultiplied_color')


def shadow_bytes(value, alpha_byte, strength, model, color=(81, 211, 239)):
    gain = value*Fraction(strength)
    if model in ('byte_gain_floor', 'premultiplied_color'):
        gain = gain.numerator//gain.denominator
    elif model == 'byte_gain_nearest':
        gain = int(gain+Fraction(1, 2))
    elif model != 'continuous_gain':
        raise ValueError('Unknown gain construction')
    if model == 'premultiplied_color':
        premultiplied = [(2*c*alpha_byte+255)//510 for c in color] + [alpha_byte]
        return [int(min(Fraction(255), gain)*Fraction(c, 255)+Fraction(1, 2)) for c in premultiplied]
    effective = min(Fraction(255), gain)*Fraction(alpha_byte, 255)
    return [int(effective*Fraction(c, 255)+Fraction(1, 2)) for c in (*color, 255)]


def compose(original, shadow, hidden):
    return shadow if hidden else [original+v*(256-original)//256 for v in shadow]


def decode(native, heldout=False):
    build = json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() == build['source_sha256']
    events = [s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    grid = itertools.product((1137375, 16712064, 0, 16777215), (0.25, 0.625), (0.5, 1.25, 3), range(2)) if heldout else itertools.product((0x51D3EF,), (0.5, 0.75, 1), (0.75, 1, 2.5), range(2))
    assert len(events) == (241 if heldout else 91) and events[-1][6:] == ['done', 'ok']
    for i, row in enumerate(events):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    result = []
    for i, (color, alpha, strength, hidden) in enumerate(grid):
        rows = events[i*5:i*5+5]
        assert rows[0][6] == 'case'
        key = list(map(float, rows[0][7].split(',')))
        alpha_byte = math.floor(alpha*255)
        assert key == [i, alpha, strength, hidden, float(format(alpha_byte/255, '.15g')), strength, hidden, 0, 0, 0, 0, 1, color]
        case = {'key': key, 'alpha_byte': alpha_byte, 'color': tuple((color >> shift) & 255 for shift in (16, 8, 0))}
        for row, stage in zip(rows[1:], ('input', 'display_input', 'apply', 'display')):
            values = row[7].split(',')
            assert row[6] == 'row' and values[:2] == [str(i), stage] and len(values) == 514
            case[stage] = unpack(list(map(int, values[2:])))
        result.append(case)
    return result


def heldout_crossed():
    from tools.probes.analyze_shadow_crossed_parameters import decode as crossed_decode, render, source, sample
    from tools.probes.analyze_shadow_phase_paths import shift_apply
    cases = crossed_decode(ROOT/'evidence/importer-loud-fail/r78/native')
    score = {'exact': 0, 'samples': 0, 'failures': []}
    blurred, shifted = {}, {}
    partitions = {}
    for case in cases:
        i, kernel, alpha, pattern, quality, filter_alpha, strength, angle, distance, *_ = case['key']
        image = source(int(alpha), int(pattern))
        key = (kernel, alpha, pattern, quality)
        if key not in blurred:
            blurred[key] = render(image, kernel, kernel, int(quality), 'grouped')
        phase_key = (*key, angle, distance)
        if phase_key not in shifted:
            shifted[phase_key] = sample(shift_apply(blurred[key], angle, distance))
        part_key = (filter_alpha, strength, angle, distance)
        if part_key not in partitions:
            partitions[part_key] = {'filter_alpha': filter_alpha, 'strength': strength, 'angle': angle, 'distance': distance, 'exact': 0, 'samples': 0}
        part = partitions[part_key]
        for index, (a, b, target) in enumerate(zip(sample(image), shifted[phase_key], case['filtered'])):
            actual = compose(a, shadow_bytes(b, case['observed_alpha_byte'], strength, 'premultiplied_color'), False)
            score['samples'] += 1
            part['samples'] += 1
            if actual == target:
                score['exact'] += 1
                part['exact'] += 1
            else:
                score['failures'].append({'case': int(i), 'index': index, 'kernel': kernel, 'quality': quality,
                    'filter_alpha': filter_alpha, 'strength': strength, 'angle': angle, 'distance': distance, 'actual': actual, 'native': target})
    score['partitions'] = list(partitions.values())
    return score


def analyze_ramps(native, heldout=False):
    scores = {model: {path: {'exact': 0, 'samples': 0, 'failures': []} for path in ('apply', 'display')} for model in MODELS}
    input_exact = pair_exact = 0
    for case in decode(native, heldout):
        i, _, strength, hidden, *_ = case['key']
        for stage in ('input', 'display_input'):
            assert case[stage] == [[v]*4 for v in range(256)]
            input_exact += 256
        pair_exact += sum(a == b for a, b in zip(case['apply'], case['display']))
        for model, paths in scores.items():
            for value in range(256):
                actual = compose(value, shadow_bytes(value, case['alpha_byte'], strength, model, case['color']), bool(hidden))
                for path, score in paths.items():
                    score['samples'] += 1
                    if actual == case[path][value]:
                        score['exact'] += 1
                    else:
                        score['failures'].append({'case': int(i), 'source_alpha': value, 'hidden': bool(hidden), 'actual': actual, 'native': case[path][value]})
    return {'input_exact': input_exact, 'native_api_pair_exact': pair_exact,
            'native_api_pair_samples': input_exact//2, 'scores': scores,
            'gain_ramp_passed': all(not s['failures'] for s in scores['premultiplied_color'].values())}


def analyze(native, colors):
    ramps = analyze_ramps(native)
    heldout = analyze_ramps(colors, True)
    crossed = heldout_crossed()
    return {'ramps': ramps, 'heldout_colors': heldout, 'heldout_r78': crossed,
            'candidate_passed': ramps['gain_ramp_passed'] and heldout['gain_ramp_passed'] and not crossed['failures'],
            'production_admitted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--colors', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report = analyze(args.native, args.colors)
    args.output.write_text(json.dumps(report, separators=(',', ':'))+'\n')
    print({k: v for k, v in report.items() if isinstance(v, bool)})
    for name in ('ramps', 'heldout_colors'):
        print(name, {m: {p: (s['exact'], s['samples']) for p, s in paths.items()} for m, paths in report[name]['scores'].items()})
    print('r78', report['heldout_r78']['exact'], report['heldout_r78']['samples'])
