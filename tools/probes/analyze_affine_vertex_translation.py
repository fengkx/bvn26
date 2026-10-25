"""Compare fixed vertex/translation operation orders with explicit native bounds."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack

FAMILIES = ('consume_translation_first', 'combine_then_even', 'child_then_draw',
            'twip_child_then_draw', 'vertex_then_translation')


def quarter(value):
    return Fraction(round(value * 4), 4)


def coordinate(local, child, draw, family):
    if family == 'consume_translation_first':
        return quarter(local + quarter(child) + draw)
    if family == 'combine_then_even':
        return quarter(local + child + draw)
    if family == 'child_then_draw':
        return quarter(local + child) + draw
    if family == 'twip_child_then_draw':
        return quarter(local + Fraction(math.trunc(child * 20), 20)) + draw
    assert family == 'vertex_then_translation'
    return quarter(local) + quarter(child) + draw


def decode(native):
    source, cases = [], []
    for kind, payload in events(native):
        v = payload.split(',')
        if kind == 'source':
            assert int(v[0]) == len(source) // 64 and len(v) == 129
            source.extend(unpack(list(map(int, v[1:]))))
        elif kind == 'case':
            assert len(v) == 36 and int(v[0]) == len(cases)
            cases.append({'key': v, 'pixels': []})
        elif kind == 'row':
            case = cases[-1]
            left, top, width, height = map(int, case['key'][26:30])
            assert int(v[0]) == top + len(case['pixels']) // width
            assert len(v) == 1 + width * 2
            case['pixels'].extend(unpack(list(map(int, v[1:]))))
        else:
            assert [kind, payload] == ['done', 'ok']
    assert source == [[144, 120, 8, 255]] * 4096 and len(cases) == 768
    for case in cases:
        left, top, w, h, ux, uy, uw, uh = map(int, case['key'][26:34])
        if not (len(case['pixels']) == w * h and
                0 <= left <= ux < ux + uw <= left + w <= 128 and
                0 <= top <= uy < uy + uh <= top + h <= 128):
            raise ValueError(f"case{case['key'][0]}: incomplete translation capture")
    return cases


def analyze(native):
    cases = decode(native)
    scores, pairs, properties = {}, [], []
    for i in range(0, len(cases), 2):
        a, b = cases[i:i + 2]
        assert a['key'][1] == b['key'][1] and a['key'][3:30] == b['key'][3:30]
        pairs.append({'case': int(a['key'][1]), 'samples': len(a['pixels']),
                      'exact': sum(p == q for p, q in zip(a['pixels'], b['pixels']))})
    for case in cases:
        k = case['key']
        scale = Fraction(k[3]); edge, step = map(int, k[4:6])
        authored = list(map(Fraction, k[6:10]))
        local = list(map(Fraction, k[10:14]))
        expected = list(map(Fraction, (8, 25, 8, 21)))
        expected[edge] += Fraction(step, 20)
        assert authored == local == expected
        a, b, c, d, cx, cy = map(Fraction, k[14:20])
        da, db, dc, dd, dx, dy = map(Fraction, k[20:26])
        shift, draw_shift = map(Fraction, k[34:36])
        assert [a, b, c, d] == [scale, 0, 0, scale]
        assert [da, db, dc, dd] == [1, 0, 0, 1]
        consumed_shift = Fraction(math.trunc(shift * 20), 20)
        assert [cx, cy] == ([consumed_shift, 0] if edge < 2 else [0, consumed_shift])
        properties.append({'case': int(k[0]), 'declared': str(shift), 'readback': str(consumed_shift)})
        assert [dx, dy] == ([40 + draw_shift, 40] if edge < 2 else [40, 40 + draw_shift])
        left, top, width, height = map(int, k[26:30])
        for family in FAMILIES:
            x0, x1 = sorted(int(coordinate(v * scale, cx, dx, family) * 4) for v in local[:2])
            y0, y1 = sorted(int(coordinate(v * scale, cy, dy, family) * 4) for v in local[2:])
            score = scores.setdefault(family, {'samples': 0, 'exact': 0,
                                               'max_channel_delta': 0, 'failures': []})
            for i, pixel in enumerate(case['pixels']):
                x, y = left + i % width, top + i // width
                count = max(0, min(4*x+4, x1)-max(4*x, x0)) * max(0, min(4*y+4, y1)-max(4*y, y0))
                actual = [v * count // 16 for v in (144, 120, 8, 255)]
                score['samples'] += 1; score['exact'] += actual == pixel
                score['max_channel_delta'] = max(score['max_channel_delta'], max(abs(p-q) for p,q in zip(actual,pixel)))
                if actual != pixel:
                    score['failures'].append({'case': int(k[0]), 'x': x, 'y': y,
                                              'actual': actual, 'native': pixel})
    return {'source_texels_exact': 4096, 'cases': len(cases), 'bounds_and_properties_exact': len(cases),
            'translation_readbacks': properties, 'storage_pairs': pairs, 'scores': scores, 'coverage_admitted': False,
            'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    for name, score in result['scores'].items():
        print(name, score['exact'], score['samples'], score['max_channel_delta'])
