"""Reject packed arithmetic against independently varied alphas and actual source bytes."""
import argparse
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_matrix_coefficient_pairs import f32
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.run_nested_filters import unpack
from tools.probes.matrix_packed_candidate import render


def decode(native):
    cases = []
    matrix = None
    for kind, payload in events(native):
        values = payload.split(',')
        if kind == 'matrix':
            assert matrix is None and len(values) == 20
            matrix = list(map(float, values))
        elif kind == 'case':
            key = list(map(int, values))
            assert len(key) == 6 and key[0] == len(cases)
            cases.append({'key': key})
        elif kind in ('source', 'filtered'):
            assert kind not in cases[-1] and len(values) == cases[-1]['key'][3]*2
            cases[-1][kind] = unpack(list(map(int, values)))
        else:
            assert [kind, payload] == ['done', 'ok']
    original = json.loads((ROOT/'evidence/importer-loud-fail/r195/native/frame3/build.json').read_text())['case']['placement']['filters'][0]['matrix']
    assert matrix == [float(format(f32(x), '.15g')) for x in original]
    assert len(cases) == 13824
    for case in cases:
        _, alpha, color, width, target, neighbor = case['key']
        assert 0 <= alpha <= 255 and color in (0, 1, 2)
        assert width in (3, 4, 5) and target in (0, width-1) and neighbor in (0, 127, 255)
        for x, pixel in enumerate(case['source']):
            if x == target:
                assert pixel[3] == alpha and all(0 <= c <= alpha for c in pixel[:3])
            else:
                assert pixel == [0, 0, 0, neighbor]
    return matrix, cases


def analyze(native):
    matrix, cases = decode(native)
    result = {'samples': 0, 'exact': 0, 'max_channel_delta': 0, 'failures': []}
    for case in cases:
        width = case['key'][3]
        output = render(case['source'], width, matrix)
        for x, (actual, expected) in enumerate(zip(output, case['filtered'])):
            result['samples'] += 1
            result['exact'] += actual == expected
            result['max_channel_delta'] = max(result['max_channel_delta'], max(abs(a-b) for a, b in zip(actual, expected)))
            if actual != expected:
                result['failures'].append({'case': case['key'], 'x': x, 'source': case['source'], 'actual': actual, 'native': expected})
    return {'matrix': matrix, 'cases': cases, 'comparison': result,
            'input_readbacks_retained': True, 'old_scalar_ramp_input_proof_pending': True,
            'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print({k: v for k, v in result['comparison'].items() if k != 'failures'})
