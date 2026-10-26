"""Keep coefficient properties distinct from candidate consumption and byte rounding."""
import argparse
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_matrix_binary_pairs import score
from tools.probes.run_nested_filters import unpack

COEFFICIENTS = [center + delta / 8192 for center in (.5, 1, 2) for delta in range(-4, 5)]


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
    assert len(cases) == len(COEFFICIENTS)*256*2
    for case in cases:
        _, ci, axis, value, neighbor = case['key']
        assert axis == 1 and neighbor in (0, 255)
        expected = [0, COEFFICIENTS[ci], 0, 0, 0, 0, 1, 0, 0, 0,
                    0, 0, 1, 0, 0, 0, 0, 0, 1, 0]
        assert case['matrix'] == expected
        assert case['source'] == [[0, value, 0, 255], [0, 0, 0, neighbor], [0]*4, [0]*4]
    return cases


def analyze(native):
    cases = decode(native)
    groups = []
    for ci, coefficient in enumerate(COEFFICIENTS):
        for neighbor in (0, 255):
            rows = [c for c in cases if c['key'][1] == ci and c['key'][4] == neighbor]
            assert [c['key'][3] for c in rows] == list(range(256))
            groups.append({'coefficient': coefficient, 'neighbor_alpha': neighbor,
                           'red_ramp': [c['filtered'][0][0] for c in rows]})
    candidates = {}
    for bits in (None, 8, 9, 10, 11, 12, 13, 16):
        for center in (False, True):
            candidates[f'{bits}/{center}'] = score(cases, bits, center)
    return {'cases': cases, 'source_pixels_exact': len(cases)*4, 'ramps': groups,
            'identity_other_channels_exact': sum(c['filtered'][0][1:] == c['source'][0][1:] for c in cases),
            'candidates': candidates, 'arithmetic_admitted': False,
            'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print({key: value['exact_red'] for key, value in result['candidates'].items()})
