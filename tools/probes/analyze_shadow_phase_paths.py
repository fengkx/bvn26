"""Discriminate signed parameterization and native filter paths without fitted phase rules."""
import argparse
from decimal import Decimal, localcontext, ROUND_HALF_UP
import hashlib
import itertools
import json
import math
from pathlib import Path
from tools.probes.analyze_blur_kernel_heldout import ROOT
from tools.probes.run_nested_filters import unpack

ROUTES = ((0, -1), (180, 1), (0, 1), (180, -1), (90, -1), (-90, 1), (90, 1), (-90, -1))
PATHS = ('apply', 'bitmap_display', 'vector_display')
RULES = ('away', 'positive', 'even')


def phase_components(angle, distance, rule):
    values = [v*distance*256 for v in (math.cos(math.radians(angle)), math.sin(math.radians(angle)))]
    if rule == 'away':
        phase = [int(math.copysign(math.floor(abs(v)+0.5), v)) for v in values]
    elif rule == 'positive':
        phase = [math.floor(v+0.5) for v in values]
    elif rule == 'even':
        phase = [round(v) for v in values]
    else:
        raise ValueError('Unknown global phase construction')
    return phase


def impulse(angle, distance, rule):
    phase = phase_components(angle, distance, rule)
    ix, iy = [v//256 for v in phase]
    fx, fy = [v%256 for v in phase]
    weights = [(256-fx)*(256-fy)//256, fx*(256-fy)//256, (256-fx)*fy//256]
    weights.append(256-sum(weights))
    pixels = [0]*49
    for (dx, dy), weight in zip(((0, 0), (1, 0), (0, 1), (1, 1)), weights):
        x, y = 3+ix+dx, 3+iy+dy
        assert 0 <= x < 7 and 0 <= y < 7
        pixels[y*7+x] = 255*weight//256
    return pixels


def shift_apply(image, angle, distance):
    phase = phase_components(angle, distance, 'even')
    ix, iy = [v//256 for v in phase]
    fx, fy = [v%256 for v in phase]
    weights = [(256-fx)*(256-fy)//256, fx*(256-fy)//256, (256-fx)*fy//256]
    weights.append(256-sum(weights))
    result = []
    height, width = len(image), len(image[0])
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


def heldout_unit_controls():
    # Native API identity is fixed by the r78 source, never selected from a pixel.
    from tools.probes.analyze_shadow_crossed_parameters import decode as crossed_decode, render, source, sample, compose
    cases = crossed_decode(ROOT/'evidence/importer-loud-fail/r78/native')
    exact = total = 0
    failures = []
    for case in cases:
        i, kernel, alpha, pattern, quality, filter_alpha, strength, angle, distance, *_ = case['key']
        if filter_alpha != 1 or strength != 1:
            continue
        image = source(int(alpha), int(pattern))
        blurred = render(image, kernel, kernel, int(quality), 'grouped')
        shifted = sample(shift_apply(blurred, angle, distance))
        for index, (a, b, target) in enumerate(zip(sample(image), shifted, case['filtered'])):
            actual = compose(a, b, 1, 1)
            total += 1
            if actual == target:
                exact += 1
            else:
                failures.append({'case': int(i), 'index': index, 'actual': actual, 'native': target})
    return {'exact': exact, 'samples': total, 'failures': failures, 'native_api': 'BitmapData.applyFilter'}


def decode(native):
    build = json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() == build['source_sha256']
    events = [s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    assert len(events) == 1729 and events[-1][6:] == ['done', 'ok']
    for i, row in enumerate(events):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    result = []
    grid = itertools.product((8, 32), range(8), (0.5, 1.5, 31.5, 127.5, 128.5, 129.5), (-1, 0, 1))
    for i, (origin, route, half, delta) in enumerate(grid):
        angle, sign = ROUTES[route]
        distance = sign*(half/256+delta/65536)
        with localcontext() as context:
            context.prec = 15
            context.rounding = ROUND_HALF_UP
            serialized = float(+Decimal.from_float(distance))
        rows = events[i*6:i*6+6]
        assert rows[0][6] == 'case'
        key = list(map(float, rows[0][7].split(',')))
        assert key == [i, origin, route, half, delta, angle, serialized, angle, serialized, 1, 0, 0, 1, 1, 1]
        case = {'key': key, 'distance_exact': distance}
        for row, stage in zip(rows[1:], ('input', 'vector_input', *PATHS)):
            values = row[7].split(',')
            assert row[6] == 'pixels' and values[:2] == [str(i), stage] and len(values) == 100
            case[stage] = unpack(list(map(int, values[2:])))
        result.append(case)
    return result


def analyze(native):
    cases = decode(native)
    scores = {rule: {path: {'exact_images': 0, 'images': len(cases), 'exact_pixels': 0, 'pixels': len(cases)*49, 'failures': []}
                     for path in PATHS} for rule in RULES}
    input_exact = 0
    original = [[255]*4 if i == 24 else [0]*4 for i in range(49)]
    for case in cases:
        for stage in ('input', 'vector_input'):
            assert case[stage] == original
            input_exact += 49
        for rule, paths in scores.items():
            predicted = [[a]*4 for a in impulse(case['key'][7], case['distance_exact'], rule)]
            for path, score in paths.items():
                target = case[path]
                score['exact_images'] += predicted == target
                for i, (p, q) in enumerate(zip(predicted, target)):
                    if p == q:
                        score['exact_pixels'] += 1
                    else:
                        score['failures'].append({'case': int(case['key'][0]), 'index': i, 'key': case['key'][1:9], 'actual': p, 'native': q})
    pairs = {}
    for a, b in (('apply', 'bitmap_display'), ('apply', 'vector_display'), ('bitmap_display', 'vector_display')):
        pairs[a+'/'+b] = {'exact_images': sum(c[a] == c[b] for c in cases), 'images': len(cases)}
    lookup = {tuple(c['key'][1:5]): c for c in cases}
    equivalence = {}
    for path in PATHS:
        matches = total = origin_matches = 0
        for origin, half, delta in itertools.product((8, 32), (0.5, 1.5, 31.5, 127.5, 128.5, 129.5), (-1, 0, 1)):
            for a, b in ((0, 1), (2, 3), (4, 5), (6, 7)):
                matches += lookup[(origin, a, half, delta)][path] == lookup[(origin, b, half, delta)][path]
                total += 1
        for route, half, delta in itertools.product(range(8), (0.5, 1.5, 31.5, 127.5, 128.5, 129.5), (-1, 0, 1)):
            origin_matches += lookup[(8, route, half, delta)][path] == lookup[(32, route, half, delta)][path]
        equivalence[path] = {'parameterization_exact': matches, 'parameterization_pairs': total,
                             'origin_exact': origin_matches, 'origin_pairs': len(cases)//2}
    old = {}
    references = []
    for name in ('shadow-phase-native.json', 'shadow-phase-sweep-native.json', 'shadow-phase-ties-native.json'):
        references.extend(json.loads((ROOT/'tools/probes/flash_filters'/name).read_text()))
    for rule in RULES:
        old[rule] = {'exact_images': sum(impulse(r['observed_angle'], r['observed_distance'], rule) == r['pixels'] for r in references), 'images': len(references)}
    admitted = [rule for rule in RULES if old[rule]['exact_images'] == old[rule]['images'] and
                all(s['exact_images'] == s['images'] for s in scores[rule].values())]
    heldout = heldout_unit_controls()
    qualified = (scores['even']['apply']['exact_images'] == len(cases) and
                 all(scores['away'][path]['exact_images'] == len(cases) for path in ('bitmap_display', 'vector_display')) and
                 old['away']['exact_images'] == old['away']['images'] and not heldout['failures'])
    return {'input_exact': input_exact, 'scores': scores, 'native_path_pairs': pairs,
            'native_equivalence': equivalence, 'old_phase': old, 'common_models_passed': admitted,
            'heldout_r78_unit': heldout, 'api_specific_phase_passed': qualified,
            'production_admitted': False, 'scope': 'No-blur unit-gain source-hidden impulses only; no runtime hidden-source support is admitted.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report = analyze(args.native)
    args.output.write_text(json.dumps(report, separators=(',', ':'))+'\n')
    print({r: {p: (v['exact_images'], v['images']) for p, v in paths.items()} for r, paths in report['scores'].items()})
    print(report['native_path_pairs'], report['native_equivalence'], report['old_phase'])
    print(report['heldout_r78_unit'])
