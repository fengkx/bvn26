"""Check explicit colored filter buffers across independently materialized opacity boundaries."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from tools.probes.analyze_blur_kernel_heldout import ROOT
from tools.probes.analyze_shadow_colored_paths import decode as colored_decode
from tools.probes.run_nested_filters import unpack
from tools.probes.normal_composition import over
from tools.probes.nested_composition import rgba

CONFIGS = ((1137375, 135, 2, 3.99609375, 3, 135, 1.25, 0.75, 2.5),
           (16712064, 25, 0, 8.25, 1, 0, -0.501953125, 0.5, 0.75))
STAGES = ('input', 'middle', 'back', 'filtered', 'child', 'parent', 'final')


def decode(native):
    build = json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest() == build['source_sha256']
    events = [s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    grid = list(itertools.product(range(2), range(2), (0, 1, 64, 128, 254, 255), (1, 25, 50, 99, 100), (25, 50, 100)))
    assert len(events) == len(grid)*8+1 and events[-1][6:] == ['done', 'ok']
    for i, row in enumerate(events):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
    cases = []
    for i, (config, api, alpha, child, parent) in enumerate(grid):
        block = events[i*8:i*8+8]
        assert block[0][6] == 'case'
        key = list(map(float, block[0][7].split(',')))
        _, _, _, kernel, quality, angle, distance, fa, strength = CONFIGS[config]
        assert key == [i, config, api, alpha, child, parent, float(format(math.floor(fa*255)/255, '.15g')), strength, kernel, kernel, quality, angle, distance]
        case = {'key': key}
        for row, stage in zip(block[1:], STAGES):
            fields = row[7].split(',')
            assert row[6] == 'row' and fields[:2] == [str(i), stage] and len(fields) == 258
            case[stage] = unpack(list(map(int, fields[2:])))
        cases.append(case)
    return cases


def filtered_references():
    result = {}
    for case in colored_decode(ROOT/'evidence/importer-loud-fail/r82/native'):
        _, kernel, alpha, pattern, quality, fa, strength, angle, distance, *_ = case['key']
        identity = (int(case['key'][-1]), int(alpha), int(pattern), kernel, int(quality), angle, distance, fa, strength)
        if identity in CONFIGS:
            index = CONFIGS.index(identity)
            for api, stage in enumerate(('filtered', 'display')):
                assert (index, api) not in result
                result[index, api] = {'input': case['input'], 'filtered': case[stage]}
    assert len(result) == 4
    return result


def shade(pixel, opacity):
    return [c*(opacity*256//100)//256 for c in pixel]


def analyze(native):
    refs = filtered_references()
    scores = {s: {'samples': 0, 'exact': 0, 'failures': []} for s in STAGES}
    collapsed_exact = 0
    for case in decode(native):
        i, config, api, alpha, child_op, parent_op, *_ = case['key']
        ref = refs[int(config), int(api)]
        middle, back = rgba(0x3355cc, int(64)), rgba(0x81d3ef, int(alpha))
        child = [shade(p, int(child_op)) for p in ref['filtered']]
        parent = [over(middle, p) for p in child]
        final = [over(back, shade(p, int(parent_op))) for p in parent]
        expected = {'input': ref['input'], 'filtered': ref['filtered'], 'middle': [middle]*128,
                    'back': [back]*128, 'child': child, 'parent': parent, 'final': final}
        combined = (int(child_op)*256//100)*(int(parent_op)*256//100)//256
        for p, target in zip(ref['filtered'], case['final']):
            collapsed = over(back, over(shade(middle, int(parent_op)), [c*combined//256 for c in p]))
            collapsed_exact += collapsed == target
        for stage, score in scores.items():
            for index, (p, q) in enumerate(zip(expected[stage], case[stage])):
                score['samples'] += 1
                if p == q:
                    score['exact'] += 1
                else:
                    score['failures'].append({'case': int(i), 'index': index, 'actual': p, 'native': q, 'key': case['key']})
    return {'scores': scores, 'collapsed_final_exact': collapsed_exact, 'collapsed_final_samples': scores['final']['samples'],
            'passed': all(not s['failures'] for s in scores.values()), 'production_admitted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = analyze(args.native)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print({k: (s['exact'], s['samples']) for k, s in result['scores'].items()})
    print({k: v for k, v in result.items() if k != 'scores'})
