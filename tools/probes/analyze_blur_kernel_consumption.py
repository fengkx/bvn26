"""Constrain kernel consumption without selecting arithmetic from output pixels."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from tools.probes.analyze_fractional_blur_axis import ROOT, decode as old_decode, source
from tools.probes.run_nested_filters import unpack

MODELS = ('unconsumed', 'fixed_four_fraction_bits', 'six_significant_bits')


def consume(kernel, model):
    if not math.isfinite(kernel) or kernel < 0:
        raise ValueError('Invalid blur kernel')
    if model == 'unconsumed':
        return kernel
    if model == 'fixed_four_fraction_bits':
        return math.floor(kernel*16)/16
    if model != 'six_significant_bits':
        raise ValueError('Unknown kernel construction')
    mantissa, exponent = math.frexp(kernel)
    return math.ldexp(math.floor(mantissa*64), exponent-6)


def axis_pass(image, kernel, vertical):
    if kernel <= 1:
        return image
    numerator, denominator = kernel.as_integer_ratio()
    unit = 2*denominator
    radius = numerator-denominator
    edge = (radius+unit-1)//unit
    weights = [(i, min(unit, max(0, radius-abs(i)*unit+unit))) for i in range(-edge, edge+1)]
    output = []
    for y in range(32):
        row = []
        for x in range(32):
            total = 0
            for i, weight in weights:
                xx, yy = (x, y+i) if vertical else (x+i, y)
                if 0 <= xx < 32 and 0 <= yy < 32:
                    total += image[yy][xx]*weight
            row.append(total//(2*numerator))
        output.append(row)
    return output


def decode(native):
    build = json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() == build['source_sha256']
    events = [s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    assert len(events) == 3403 and events[-1][6:] == ['done', 'ok']
    for i, row in enumerate(events):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    kernels = [center+offset/1024 for center in (2.0625, 3.5, 3.9375, 4, 5.0625, 7.9375, 8)
               for offset in (-17, -16, -15, -1, 0, 1, 15, 16, 17)]
    result = []
    for i, (kernel, alpha, pattern, axis) in enumerate(itertools.product(kernels, (25, 135, 255), range(2), range(3))):
        rows = events[i*3:i*3+3]
        assert rows[0][6] == 'case'
        key = list(map(float, rows[0][7].split(',')))
        assert key == [i, kernel, alpha, pattern, axis, 1 if axis == 1 else kernel, 1 if axis == 0 else kernel]
        case = {'key': key}
        for row, stage in zip(rows[1:], ('input', 'filtered')):
            values = row[7].split(',')
            assert row[6] == 'row' and values[:2] == [str(i), stage] and len(values) == 130
            case[stage] = unpack(list(map(int, values[2:])))
        result.append(case)
    return result


def sample(image, count):
    return image[16] + ([row[16] for row in image] if count == 64 else [])


def compare(cases):
    scores = {name: {'exact': 0, 'samples': 0, 'failures': []} for name in MODELS}
    input_exact = 0
    for case in cases:
        i, k, alpha, pattern, axis, bx, by = case['key']
        image = source(int(alpha), int(pattern))
        count = len(case['input'])
        assert [[a]*4 for a in sample(image, count)] == case['input']
        input_exact += count
        for model, score in scores.items():
            output = axis_pass(axis_pass(image, consume(bx, model), False), consume(by, model), True)
            for index, (value, target) in enumerate(zip(sample(output, count), case['filtered'])):
                score['samples'] += 1
                if [value]*4 == target:
                    score['exact'] += 1
                else:
                    score['failures'].append({'case': int(i), 'kernel': k, 'alpha': alpha,
                        'pattern': int(pattern), 'axis': int(axis), 'index': index, 'actual': value, 'native': target})
    return {'input_exact': input_exact, 'models': scores}


def analyze(native):
    old = compare(old_decode(ROOT/'evidence/importer-loud-fail/r71/native'))
    fresh = compare(decode(native))
    # Existing 242-case GPU fixtures must retain precisely the same kernel operands.
    prior = []
    for name in ('native-filter-rows.json', 'native-small-filter-rows.json', 'native-bounds-filter-rows.json'):
        for row in json.loads((ROOT/'evidence/importer-loud-fail'/name).read_text()):
            prior.append(row['size'] == consume(row['size'], 'six_significant_bits'))
    return {'old': old, 'fresh': fresh, 'prior_blur_operands_unchanged': {'exact': sum(prior), 'cases': len(prior)},
            'bounded_cpu_passed': all(not r['models']['six_significant_bits']['failures'] for r in (old, fresh)),
            'production_admitted': False,
            'scope': 'Explicit one-pass BlurFilter, retained source geometry; not executed instruction or implicit Glow proof.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report = analyze(args.native)
    args.output.write_text(json.dumps(report, separators=(',', ':'))+'\n')
    print({stage: {k: (v['exact'], v['samples']) for k, v in report[stage]['models'].items()} for stage in ('old', 'fresh')})
    print('bounded_cpu_passed', report['bounded_cpu_passed'], report['prior_blur_operands_unchanged'])
