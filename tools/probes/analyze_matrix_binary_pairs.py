"""Constrain input-center ordering without admitting a coefficient construction."""
import argparse
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_matrix_coefficient_pairs import decode as prior_decode
from tools.probes.run_nested_filters import unpack

COEFFICIENTS = [-2, -1, -.5, 0, .25, .5, 1, 2, 4]


def decode(native):
    cases = []
    for kind, payload in events(native):
        values = payload.split(',')
        if kind == 'case':
            key = list(map(int, values))
            assert len(key) == 5 and key[0] == len(cases)
            cases.append({'key': key})
        elif kind == 'matrix':
            assert kind not in cases[-1] and len(values) == 20
            cases[-1][kind] = list(map(float, values))
        elif kind in ('source', 'filtered'):
            assert kind not in cases[-1] and len(values) == 8
            cases[-1][kind] = unpack(list(map(int, values)))
        else:
            assert [kind, payload] == ['done', 'ok']
    assert len(cases) == 4608
    for case in cases:
        _, ci, axis, value, neighbor = case['key']
        assert axis == 1 and neighbor in (0, 255)
        coefficient = COEFFICIENTS[ci]
        offset = 128 if coefficient < 0 else 0
        expected = [0, coefficient, 0, 0, offset, 0, 1, 0, 0, 0,
                    0, 0, 1, 0, 0, 0, 0, 0, 1, 0]
        assert case['matrix'] == expected
        assert case['source'] == [[0, value, 0, 255], [0, 0, 0, neighbor], [0]*4, [0]*4]
    return cases


def predict(case, bits, center):
    _, _, axis, value, neighbor = case['key']
    coefficient = case['matrix'][axis]
    if bits is not None:
        coefficient = round(coefficient * (1 << bits)) / (1 << bits)
    source = value + (.5 if center and neighbor == 0 else 0)
    return max(0, min(255, math.floor(coefficient * source + case['matrix'][4] + .5)))


def score(cases, bits, center):
    result = {'samples': len(cases), 'exact_red': 0, 'failures': []}
    for case in cases:
        actual = predict(case, bits, center)
        expected = case['filtered'][0][0]
        result['exact_red'] += actual == expected
        if actual != expected:
            result['failures'].append({'case': case['key'], 'actual': actual, 'native': expected})
    return result


def analyze(native, prior):
    cases = decode(native)
    _, old = prior_decode(prior)
    controls = {str(center): score(cases, None, center) for center in (False, True)}
    # A shared precision grid is a rejection experiment, not a coefficient lookup.
    crossed = {str(bits): score(old, bits, True) for bits in [None, *range(8, 17)]}
    identity = sum(c['filtered'][0][1:] == c['source'][0][1:] for c in cases)
    return {'cases': cases, 'source_pixels_exact': len(cases)*4,
            'identity_other_channels_exact': identity, 'binary_controls': controls,
            'crossed_nonbinary': crossed, 'arithmetic_admitted': False,
            'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--prior', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native, args.prior)
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print({key: value['exact_red'] for key, value in result['binary_controls'].items()})
    print({key: value['exact_red'] for key, value in result['crossed_nonbinary'].items()})
