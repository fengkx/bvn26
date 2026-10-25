"""Validate non-white source composition against both independently identified native APIs."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from tools.probes.analyze_blur_kernel_heldout import ROOT, render, source, sample
from tools.probes.analyze_shadow_crossed_parameters import shift
from tools.probes.analyze_shadow_phase_paths import shift_apply
from tools.probes.analyze_shadow_gain_paths import shadow_bytes
from tools.probes.run_nested_filters import unpack

OFFSETS = ((0, 0), (0, -0.501953125), (135, 1.25))


def decode(native):
    build = json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() == build['source_sha256']
    rows = [s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    grid = list(itertools.product((1137375, 16712064), (3.99609375, 8.25), (25, 135, 254), (0, 2), (1, 3), OFFSETS, (0.5, 0.75), (0.75, 2.5)))
    assert len(rows) == len(grid)*6+1 and rows[-1][6:] == ['done', 'ok']
    for i, row in enumerate(rows):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    cases = []
    for i, (color, kernel, alpha, pattern, quality, (angle, distance), fa, strength) in enumerate(grid):
        block = rows[i*6:i*6+6]
        assert block[0][6] == 'case'
        key = list(map(float, block[0][7].split(',')))
        ab = math.floor(fa*255)
        assert key == [i, kernel, alpha, pattern, quality, fa, strength, angle, distance, kernel, kernel, quality, float(format(ab/255, '.15g')), strength, angle, distance, color]
        case = {'key': key, 'alpha_byte': ab}
        for row, stage in zip(block[1:], ('input', 'blur', 'filtered', 'display_input', 'display')):
            fields = row[7].split(',')
            assert row[6] == 'row' and fields[:2] == [str(i), stage] and len(fields) == 258
            case[stage] = unpack(list(map(int, fields[2:])))
        cases.append(case)
    return cases


def analyze(native):
    scores = {path: {'exact': 0, 'samples': 0, 'failures': []} for path in ('apply', 'display')}
    inputs = blur_exact = pairs = samples = 0
    blurred, shifted = {}, {}
    for case in decode(native):
        i, kernel, alpha, pattern, quality, fa, strength, angle, distance, *_ = case['key']
        image = source(int(alpha), int(pattern))
        assert [p[3] for p in case['input']] == sample(image)
        assert all(0 <= c <= p[3] for p in case['input'] for c in p[:3])
        inputs += sum(a == b for a, b in zip(case['input'], case['display_input']))
        pairs += sum(a == b for a, b in zip(case['filtered'], case['display']))
        key = (kernel, alpha, pattern, quality)
        if key not in blurred:
            blurred[key] = render(image, kernel, kernel, int(quality), 'grouped')
        blur_exact += sum(a == b[3] for a, b in zip(sample(blurred[key]), case['blur']))
        samples += 128
        for path, shift_fn, target_stage in (('apply', shift_apply, 'filtered'), ('display', shift, 'display')):
            phase_key = (*key, angle, distance, path)
            if phase_key not in shifted:
                shifted[phase_key] = sample(shift_fn(blurred[key], angle, distance))
            score = scores[path]
            for index, (base, a, target) in enumerate(zip(case['input'], shifted[phase_key], case[target_stage])):
                shadow = shadow_bytes(a, case['alpha_byte'], strength, 'premultiplied_color')
                actual = [c+s*(256-base[3])//256 for c, s in zip(base, shadow)]
                score['samples'] += 1
                if actual == target:
                    score['exact'] += 1
                else:
                    score['failures'].append({'case': int(i), 'index': index, 'source': base, 'shadow_alpha': a, 'actual': actual, 'native': target, 'params': case['key']})
    return {'input_api_pairs_exact': inputs, 'blur_alpha_exact': blur_exact, 'samples': samples,
            'output_api_pairs_exact': pairs, 'scores': scores,
            'passed': inputs == samples and blur_exact == samples and all(not s['failures'] for s in scores.values()),
            'production_admitted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    r = analyze(args.native)
    args.output.write_text(json.dumps(r, separators=(',', ':'))+'\n')
    print({k: v for k, v in r.items() if k != 'scores'})
    print({k: (s['exact'], s['samples']) for k, s in r['scores'].items()})
