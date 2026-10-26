"""Test one common kernel rule at held-out exponents and filter pass counts."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
from tools.probes.analyze_blur_kernel_consumption import ROOT, consume, decode as prior_decode
from tools.probes.analyze_fractional_blur_axis import decode as old_decode, source as old_source
from tools.probes.run_nested_filters import unpack


def axis_pass(image, kernel, vertical):
    if kernel <= 1:
        return image
    numerator, denominator = kernel.as_integer_ratio()
    unit = 2*denominator
    radius = numerator-denominator
    edge = (radius+unit-1)//unit
    edge_weight = radius-edge*unit+unit
    lines = list(zip(*image)) if vertical else image
    result = []
    for line in lines:
        prefix = [0]
        for value in line:
            prefix.append(prefix[-1]+value)
        size = len(line)
        row = []
        for x in range(size):
            total = unit*(prefix[min(size, x+edge)]-prefix[max(0, x-edge+1)])
            for at in (x-edge, x+edge):
                if 0 <= at < size:
                    total += edge_weight*line[at]
            row.append(total//(2*numerator))
        result.append(row)
    return [list(row) for row in zip(*result)] if vertical else result


def render(image, bx, by, quality, order):
    bx, by = [consume(k, 'six_significant_bits') for k in (bx, by)]
    if order == 'alternating':
        axes = [False, True]*quality
    elif order == 'grouped':
        axes = [False]*quality+[True]*quality
    elif order == 'grouped_vertical_first':
        axes = [True]*quality+[False]*quality
    else:
        raise ValueError('Unknown pass order')
    for vertical in axes:
        image = axis_pass(image, by if vertical else bx, vertical)
    return image


def sample(image, columns=True):
    center = len(image)//2
    return image[center]+([row[center] for row in image] if columns else [])


def source(alpha, pattern):
    return [[(alpha if pattern == 0 else (alpha if x == y == 32 else 0) if pattern == 1 else alpha*(x-24)//16)
             if 24 <= x < 41 and 24 <= y < 41 else 0 for x in range(64)] for y in range(64)]


def decode(native):
    build = json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() == build['source_sha256']
    events = [s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    assert len(events) == 3889 and events[-1][6:] == ['done', 'ok']
    for i, row in enumerate(events):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    kernels = [center+offset/1024 for center in (0.5, 1, 1.5, 2, 8.25, 15.5, 16, 16.25) for offset in (-1, 0, 1)]
    result = []
    for i, (kernel, alpha, pattern, axis, quality) in enumerate(itertools.product(kernels, (25, 135), range(3), range(3), (1, 2, 3))):
        rows = events[i*3:i*3+3]
        assert rows[0][6] == 'case'
        key = list(map(float, rows[0][7].split(',')))
        assert key == [i, kernel, alpha, pattern, axis, 1 if axis == 1 else kernel, 1 if axis == 0 else kernel, quality, quality]
        case = {'key': key}
        for row, stage in zip(rows[1:], ('input', 'filtered')):
            values = row[7].split(',')
            assert row[6] == 'row' and values[:2] == [str(i), stage] and len(values) == 258
            case[stage] = unpack(list(map(int, values[2:])))
        result.append(case)
    return result


def analyze(native):
    regression = {}
    for name, reader in [('r71', old_decode), ('r72', prior_decode)]:
        exact = total = 0
        for case in reader(ROOT/'evidence/importer-loud-fail'/name/'native'):
            _, _, alpha, pattern, _, bx, by = case['key']
            image = old_source(int(alpha), int(pattern))
            assert [[a]*4 for a in sample(image, name == 'r72')] == case['input']
            out = sample(render(image, bx, by, 1, 'alternating'), name == 'r72')
            exact += sum([v]*4 == target for v, target in zip(out, case['filtered']))
            total += len(out)
        regression[name] = {'exact': exact, 'samples': total}
    scores = {order: {'exact': 0, 'samples': 0, 'failures': []} for order in ('alternating', 'grouped', 'grouped_vertical_first')}
    input_exact = 0
    for case in decode(native):
        i, k, alpha, pattern, axis, bx, by, quality, _ = case['key']
        image = source(int(alpha), int(pattern))
        assert [[a]*4 for a in sample(image)] == case['input']
        input_exact += 128
        for order, score in scores.items():
            out = sample(render(image, bx, by, int(quality), order))
            for index, (value, target) in enumerate(zip(out, case['filtered'])):
                score['samples'] += 1
                if [value]*4 == target:
                    score['exact'] += 1
                else:
                    score['failures'].append({'case': int(i), 'kernel': k, 'alpha': alpha,
                        'pattern': int(pattern), 'axis': int(axis), 'quality': int(quality),
                        'index': index, 'actual': value, 'native': target})
    return {'input_exact': input_exact, 'regressions': regression, 'orders': scores,
            'bounded_cpu_passed': all(r['exact'] == r['samples'] for r in regression.values()) and not scores['grouped']['failures'],
            'current_production_order_passed': not scores['alternating']['failures'],
            'production_admitted': False, 'scope': 'Explicit BitmapData BlurFilter, bounded source/support; no implicit Glow or production admission.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report = analyze(args.native)
    args.output.write_text(json.dumps(report, separators=(',', ':'))+'\n')
    print(report['regressions'], 'input', report['input_exact'])
    print({k: (v['exact'], v['samples']) for k, v in report['orders'].items()})
    print('bounded_cpu_passed', report['bounded_cpu_passed'])
