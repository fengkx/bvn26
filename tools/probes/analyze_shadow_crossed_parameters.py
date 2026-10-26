"""Cross the pinned shadow phase rule with multi-pass blur and non-unit filter parameters."""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
from tools.probes.analyze_blur_kernel_heldout import ROOT, render, sample, source
from tools.probes.run_nested_filters import unpack

OFFSETS = ((0, 0), (45, 0.375), (45, -0.375), (0, -0.501953125), (135, 1.25))


def shift(image, angle, distance):
    radians = math.radians(angle)
    phase = [int(math.copysign(math.floor(abs(component*distance)*256+0.5), component*distance))
             for component in (math.cos(radians), math.sin(radians))]
    ix, iy = [v//256 for v in phase]
    fx, fy = [v%256 for v in phase]
    weights = [(256-fx)*(256-fy)//256, fx*(256-fy)//256, (256-fx)*fy//256]
    weights.append(256-sum(weights))
    height, width = len(image), len(image[0])
    result = []
    for y in range(height):
        row = []
        for x in range(width):
            total = 0
            for (dx, dy), weight in zip(((0, 0), (1, 0), (0, 1), (1, 1)), weights):
                xx, yy = x-ix-dx, y-iy-dy
                if 0 <= xx < width and 0 <= yy < height:
                    total += image[yy][xx]*weight
            row.append(total//256)
        result.append(row)
    return result


def compose(original_alpha, shadow_alpha, filter_alpha, strength):
    # The current shared operation sequence, evaluated exactly rather than with an epsilon.
    effective = min(Fraction(255), shadow_alpha*Fraction(strength))*Fraction(filter_alpha)
    glow = [int(effective*Fraction(channel, 255)+Fraction(1, 2)) for channel in (81, 211, 239, 255)]
    return [original_alpha+value*(256-original_alpha)//256 for value in glow]


def decode(native):
    build = json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() == build['source_sha256']
    events = [s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    assert len(events) == 6481 and events[-1][6:] == ['done', 'ok']
    for i, row in enumerate(events):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    grid = itertools.product((3.99609375, 7.99609375, 8.25), (25, 135), range(3), (1, 3), OFFSETS, (0.5, 0.75, 1), (0.75, 1, 2.5))
    result = []
    for i, (kernel, alpha, pattern, quality, (angle, distance), filter_alpha, strength) in enumerate(grid):
        rows = events[i*4:i*4+4]
        assert rows[0][6] == 'case'
        key = list(map(float, rows[0][7].split(',')))
        alpha_byte = math.floor(filter_alpha*255)
        observed_alpha = float(format(alpha_byte/255, '.15g'))
        assert key == [i, kernel, alpha, pattern, quality, filter_alpha, strength, angle, distance,
                       kernel, kernel, quality, observed_alpha, strength, angle, distance]
        case = {'key': key, 'observed_alpha_byte': alpha_byte}
        for row, stage in zip(rows[1:], ('input', 'blur', 'filtered')):
            values = row[7].split(',')
            assert row[6] == 'row' and values[:2] == [str(i), stage] and len(values) == 258
            case[stage] = unpack(list(map(int, values[2:])))
        result.append(case)
    return result


def phase_regressions():
    scores = {}
    image = [[0]*7 for _ in range(7)]
    image[3][3] = 255
    for name in ('shadow-phase-native.json', 'shadow-phase-sweep-native.json', 'shadow-phase-ties-native.json'):
        rows = json.loads((ROOT/'tools/probes/flash_filters'/name).read_text())
        exact = 0
        for row in rows:
            actual = shift(image, row['observed_angle'], row['observed_distance'])
            exact += [v for line in actual for v in line] == row['pixels']
        scores[name] = {'exact': exact, 'cases': len(rows)}
    return scores


def analyze(native):
    scores = {stage: {'exact': 0, 'samples': 0, 'failures': []} for stage in ('input', 'blur', 'filtered', 'requested_alpha_control')}
    cache, shifted = {}, {}
    cases = decode(native)
    for case in cases:
        i, kernel, alpha, pattern, quality, filter_alpha, strength, angle, distance, *_ = case['key']
        image = source(int(alpha), int(pattern))
        key = (kernel, alpha, pattern, quality)
        if key not in cache:
            cache[key] = render(image, kernel, kernel, int(quality), 'grouped')
        offset_key = (*key, angle, distance)
        if offset_key not in shifted:
            shifted[offset_key] = sample(shift(cache[key], angle, distance))
        original = sample(image)
        predictions = {'input': [[a]*4 for a in original], 'blur': [[a]*4 for a in sample(cache[key])],
                       'filtered': [compose(a, b, Fraction(case['observed_alpha_byte'], 255), strength) for a, b in zip(original, shifted[offset_key])],
                       'requested_alpha_control': [compose(a, b, filter_alpha, strength) for a, b in zip(original, shifted[offset_key])]}
        for stage, pixels in predictions.items():
            score = scores[stage]
            for index, (actual, target) in enumerate(zip(pixels, case['filtered' if stage == 'requested_alpha_control' else stage])):
                score['samples'] += 1
                if actual == target:
                    score['exact'] += 1
                else:
                    score['failures'].append({'case': int(i), 'index': index, 'kernel': kernel, 'source_alpha': alpha,
                                              'quality': int(quality), 'filter_alpha': filter_alpha, 'strength': strength,
                                              'angle': angle, 'distance': distance, 'actual': actual, 'native': target})
    partitions = {}
    for case in cases:
        key = tuple(case['key'][5:9])
        if key not in partitions:
            partitions[key] = {'filter_alpha': key[0], 'strength': key[1], 'angle': key[2], 'distance': key[3], 'samples': 0, 'exact': 0}
        partitions[key]['samples'] += 128
        partitions[key]['exact'] += 128
    for failure in scores['filtered']['failures']:
        key = tuple(failure[k] for k in ('filter_alpha', 'strength', 'angle', 'distance'))
        partitions[key]['exact'] -= 1
    regressions = phase_regressions()
    return {'scores': scores, 'partitions': list(partitions.values()), 'phase_regressions': regressions,
            'bounded_cpu_passed': all(not scores[k]['failures'] for k in ('input', 'blur', 'filtered')) and all(s['exact'] == s['cases'] for s in regressions.values()),
            'production_admitted': False, 'scope': 'Independent explicit DropShadow controls; no GPU/production admission.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.native)
    args.output.write_text(json.dumps(report, separators=(',', ':'))+'\n')
    print({k: (v['exact'], v['samples']) for k, v in report['scores'].items()})
    print(report['phase_regressions'], 'bounded_cpu_passed', report['bounded_cpu_passed'])
