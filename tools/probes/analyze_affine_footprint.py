"""Reject globally fixed Euclidean footprint constructions against old native bytes."""
import argparse
from fractions import Fraction
from functools import lru_cache
import json
import math
from pathlib import Path

from tools.probes.analyze_affine_scale_split import property_float32
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_nearest_affine import decode, inverse
from tools.probes.run_nested_filters import unpack


FAMILIES = ('exact_inverse', 'fixed_inverse', 'fixed_inverse_offset')


def floor_surd(base, square):
    """Floor base + sqrt(square) without floating approximation or epsilon."""
    assert square >= 0
    value = math.floor(base) + math.isqrt(square.numerator // square.denominator)
    boundary = value + 1 - base
    if boundary <= 0 or boundary * boundary <= square:
        value += 1
    return value


@lru_cache(maxsize=None)
def prepare(coefficients, family):
    assert family in FAMILIES
    rows = []
    for a, b, t in coefficients:
        if family != 'exact_inverse':
            a, b, t = [Fraction(math.floor(v * 65536 + Fraction(1, 2)), 65536) for v in (a, b, t)]
        negative = min(0, a) + min(0, b)
        square = (a*a + b*b) / 4
        if family == 'fixed_inverse_offset':
            offset = Fraction(floor_surd(negative*65536 + Fraction(1, 2), square*65536**2), 65536)
            rows.append((a, b, t+offset, Fraction(0)))
        else:
            rows.append((a, b, t+negative, square))
    return rows


def indices(coefficients, x, y, family, delta=(0, 0)):
    return [floor_surd(a*x + b*y + t - d, square)
            for (a, b, t, square), d in zip(prepare(tuple(coefficients), family), delta)]


def analyze(root):
    scores = {}

    def record(suite, coeff, x, y, native, key, delta=(0, 0)):
        for family in FAMILIES:
            actual = indices(coeff, x, y, family, delta)
            s = scores.setdefault(suite+'/'+family, {'samples': 0, 'exact': 0, 'max_source_index_delta': 0, 'failures': []})
            s['samples'] += 1
            s['exact'] += actual == native
            s['max_source_index_delta'] = max(s['max_source_index_delta'], max(abs(a-b) for a,b in zip(actual,native)))
            if actual != native:
                s['failures'].append({'key': key, 'x': x, 'y': y, 'delta': list(map(str, delta)), 'actual': actual, 'native': native})

    _, cases = decode(root/'r158/native')
    for case in cases:
        co = inverse(case['key'])
        for y in range(40):
            for x in range(40):
                if not all(1 <= a*xx+b*yy+t <= 15 for a,b,t in co for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1))):
                    continue
                pixel = case['pixels'][y*40+x]
                assert pixel[2:] == [73,255] and all((v-8)%15 == 0 for v in pixel[:2])
                record('r158', co, x, y, [(v-8)//15 for v in pixel[:2]], case['key'])
    for round_number in (162,163,164,165,166,168,169):
        for kind,payload in events(root/f'r{round_number}/native'):
            if kind != 'sample':
                continue
            v = payload.split(',')
            pixel = unpack(list(map(int,v[-2:])))[0]
            assert pixel[2:] == [73,255]
            delta = [Fraction(0),Fraction(0)]
            if round_number <= 165:
                key = v[:17]
                x,y = map(int,v[19:21])
            elif round_number in (166,168):
                key = v[:17]
                axis,step = int(v[2]),int(v[3])
                x,y = map(int,v[21:23])
                delta[axis] = Fraction(math.trunc(Fraction(step,64)*20),20) if round_number == 166 else Fraction(step,64)
                if round_number == 168:
                    key[5:9] = [str(property_float32(c)*64) for c in v[5:9]]
            else:
                x,y = map(int,v[15:17])
                delta[int(v[4])] = Fraction(int(v[5]),64)
                key = ['0']*5 + [str(property_float32(c)*64) for c in v[7:11]] + ['0','0','1','0','0','1','128','128']
            record(f'r{round_number}', inverse(key), x, y, pixel[:2], v[:-2], delta)
    return {'construction': 'offset = norm(inverse_row)/2 + min(0,a) + min(0,b)',
            'square_root_comparison': 'exact rational inequalities; no float/epsilon',
            'scores': scores, 'coefficients_selected_from_intervals': False,
            'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence', type=Path, default=Path('evidence/importer-loud-fail'))
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    r = analyze(a.evidence)
    a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():
        print(k,v['exact'],v['samples'],v['max_source_index_delta'])
