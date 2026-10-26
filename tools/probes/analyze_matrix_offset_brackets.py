"""Independently shift output boundaries while retaining exact coefficient properties."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_matrix_coefficient_brackets import COEFFICIENTS, decode as prior_decode
from tools.probes.analyze_matrix_binary_pairs import score
from tools.probes.run_nested_filters import unpack

BYTES = [0, 1, 63, 64, 127, 128, 191, 192, 254, 255]
OFFSETS = [-1, -.75, -.5, -.25, 0, .25, .5, .75, 1]


def decode(native):
    cases = []
    for kind, payload in events(native):
        values = payload.split(',')
        if kind == 'case':
            assert len(values) == 6
            key = [*map(int, values[:5]), float(values[5])]
            assert key[0] == len(cases)
            cases.append({'key': key})
        elif kind == 'matrix':
            assert kind not in cases[-1] and len(values) == 20
            cases[-1][kind] = list(map(float, values))
        elif kind in ('source', 'filtered'):
            assert kind not in cases[-1] and len(values) == 8
            cases[-1][kind] = unpack(list(map(int, values)))
        else:
            assert [kind, payload] == ['done', 'ok']
    assert len(cases) == len(COEFFICIENTS)*len(BYTES)*len(OFFSETS)*2
    for case in cases:
        _, ci, axis, value, neighbor, offset = case['key']
        assert axis == 1 and neighbor in (0, 255) and value in BYTES and offset in OFFSETS
        expected = [0, COEFFICIENTS[ci], 0, 0, offset, 0, 1, 0, 0, 0,
                    0, 0, 1, 0, 0, 0, 0, 0, 1, 0]
        assert case['matrix'] == expected
        assert case['source'] == [[0, value, 0, 255], [0, 0, 0, neighbor], [0]*4, [0]*4]
    return cases


def analyze(native, prior):
    cases = decode(native)
    old = {tuple(c['key'][1:]): c for c in prior_decode(prior)}
    retained = 0
    for case in cases:
        if case['key'][-1] == 0:
            previous = old[tuple(case['key'][1:-1])]
            assert all(case[k] == previous[k] for k in ('source', 'filtered', 'matrix'))
            retained += 1
    candidates = {}
    compatible = [dict(c, key=c['key'][:5]) for c in cases]
    for bits in (None, 8, 9, 10, 11, 12, 13, 16):
        for center in (False, True):
            candidates[f'{bits}/{center}'] = score(compatible, bits, center)
    groups = defaultdict(list)
    for case in cases:
        _, ci, _, value, neighbor, offset = case['key']
        groups[(ci, neighbor)].append([value, offset, case['filtered'][0][0]])
    equal = []
    for neighbor in (0, 255):
        for center in range(3):
            for a in range(center*9, center*9+9):
                for b in range(a+1, center*9+9):
                    x, y = groups[(a, neighbor)], groups[(b, neighbor)]
                    assert [r[:2] for r in x] == [r[:2] for r in y]
                    equal.append({'neighbor_alpha': neighbor, 'coefficients': [COEFFICIENTS[a], COEFFICIENTS[b]],
                                  'equal_zero_offset': all(u[2] == v[2] for u, v in zip(x, y) if u[1] == 0),
                                  'equal_all_offsets': x == y})
    return {'cases': cases, 'source_pixels_exact': len(cases)*4, 'retained_zero_offset_cases': retained,
            'identity_other_channels_exact': sum(c['filtered'][0][1:] == c['source'][0][1:] for c in cases),
            'coefficient_equivalence': equal, 'candidates': candidates,
            'arithmetic_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--prior', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native, args.prior)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print({key: value['exact_red'] for key, value in result['candidates'].items()})
    print('retained', result['retained_zero_offset_cases'])
    print('plateaus split', sum(r['equal_zero_offset'] and not r['equal_all_offsets'] for r in result['coefficient_equivalence']))
