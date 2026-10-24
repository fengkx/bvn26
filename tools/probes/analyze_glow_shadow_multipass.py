"""Independently constrain multi-pass Glow and zero-offset DropShadow behavior."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
from tools.probes.analyze_blur_kernel_heldout import ROOT, render, sample, source
from tools.probes.run_nested_filters import unpack


def decode(native):
    build = json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() == build['source_sha256']
    events = [s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    assert len(events) == 2161 and events[-1][6:] == ['done', 'ok']
    for i, row in enumerate(events):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    grid = itertools.product((1.5, 3.99609375, 7.99609375, 8.25, 16), (25, 135), range(3), range(3), (1, 2, 3), range(2))
    result = []
    for i, (kernel, alpha, pattern, axis, quality, family) in enumerate(grid):
        rows = events[i*4:i*4+4]
        assert rows[0][6] == 'case'
        key = list(map(float, rows[0][7].split(',')))
        assert key == [i, kernel, alpha, pattern, axis, 1 if axis == 1 else kernel, 1 if axis == 0 else kernel,
                       quality, quality, family, 0x51D3EF, 1, 1]
        case = {'key': key}
        for row, stage in zip(rows[1:], ('input', 'blur', 'filtered')):
            values = row[7].split(',')
            assert row[6] == 'row' and values[:2] == [str(i), stage] and len(values) == 258
            case[stage] = unpack(list(map(int, values[2:])))
        result.append(case)
    return result


def compose(original_alpha, blurred_alpha):
    glow = [(2*blurred_alpha*channel+255)//510 for channel in (81, 211, 239)] + [blurred_alpha]
    return [original_alpha+channel*(256-original_alpha)//256 for channel in glow]


def analyze(native):
    orders = ('grouped', 'alternating', 'grouped_vertical_first')
    scores = {family: {order: {'exact': 0, 'samples': 0, 'failures': []} for order in orders}
              for family in ('glow', 'shadow_zero')}
    inputs = 0
    blur_score = {'exact': 0, 'samples': 0, 'failures': []}
    cache = {}
    for case in decode(native):
        i, kernel, alpha, pattern, axis, bx, by, quality, _, family_id, *_ = case['key']
        family = 'glow' if family_id == 0 else 'shadow_zero'
        image = source(int(alpha), int(pattern))
        original = sample(image)
        assert [[a]*4 for a in original] == case['input']
        inputs += len(original)
        for order in orders:
            key = (kernel, alpha, pattern, axis, quality, order)
            if key not in cache:
                cache[key] = sample(render(image, bx, by, int(quality), order))
            blurred = cache[key]
            if order == 'grouped':
                for index, (value, target) in enumerate(zip(blurred, case['blur'])):
                    blur_score['samples'] += 1
                    if [value]*4 == target:
                        blur_score['exact'] += 1
                    else:
                        blur_score['failures'].append({'case': int(i), 'index': index, 'actual': value, 'native': target})
            score = scores[family][order]
            for index, (a, b, target) in enumerate(zip(original, blurred, case['filtered'])):
                actual = compose(a, b)
                score['samples'] += 1
                if actual == target:
                    score['exact'] += 1
                else:
                    score['failures'].append({'case': int(i), 'kernel': kernel, 'alpha': alpha, 'pattern': int(pattern),
                                              'axis': int(axis), 'quality': int(quality), 'index': index,
                                              'actual': actual, 'native': target})
    passed = not blur_score['failures'] and all(not s['grouped']['failures'] for s in scores.values())
    return {'input_exact': inputs, 'independent_blur': blur_score, 'families': scores,
            'bounded_cpu_passed': passed, 'production_admitted': False,
            'scope': 'Explicit applyFilter, outer Glow and zero-distance DropShadow, unit alpha/strength; independent Blur is not a hidden family-buffer readback.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.native)
    args.output.write_text(json.dumps(report, separators=(',', ':'))+'\n')
    print('input', report['input_exact'], 'blur', report['independent_blur']['exact'])
    print({f: {k: (v['exact'], v['samples']) for k, v in orders.items()} for f, orders in report['families'].items()})
    print('bounded_cpu_passed', report['bounded_cpu_passed'])
