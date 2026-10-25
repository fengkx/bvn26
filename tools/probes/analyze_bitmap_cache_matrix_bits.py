"""Read binary matrix intermediates without selecting a pixel-dependent arithmetic path."""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_width import sample, compare_samples, ROOT


def number(text):
    if text == '0':
        return 0.0
    sign, exponent, digits = text.split(':')
    assert sign in ('1', '-1') and len(digits) == 53 and digits[0] == '1'
    assert set(digits) <= {'0', '1'}
    return float(int(sign) * Fraction(int(digits, 2)) * Fraction(2) ** (int(exponent) - 52))


def decode(native):
    build = json.loads((native / 'build.json').read_text())
    assert hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest() == build['source_sha256']
    path = native / 'native.log'
    text = path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    rows = [line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    assert len(rows) == 1449 and rows[-1][6:] == ['done', 'ok']
    cases = []
    inputs = 0
    for i, row in enumerate(rows):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
        kind, value = row[6:]
        if kind == 'source':
            label, width, y, *values = value.split(',')
            assert label == 'shared' and width == '16' and int(y) == inputs // 16 and len(values) == 16
            for x, v in enumerate(values):
                assert int(v) & 0xffffffff == 0xff000000 + x % 2 * 255 * 65536 + ((x * 37 + 17) % 256) * 256 + 113
                inputs += 1
        elif kind == 'case':
            key = list(map(float, value.split(',')))
            assert len(key) == 12 and key[0] == len(cases)
            cases.append({'key': key})
        elif kind == 'binary':
            values = value.split(',')
            assert len(values) == 15
            cases[-1]['binary'] = values
        elif kind == 'cache':
            assert value in ('0,false', '1,true')
        elif kind in ('clear', 'cached'):
            values = list(map(int, value.split(',')))
            assert len(values) == 1024 and kind not in cases[-1]
            cases[-1][kind] = [[(v >> shift) & 255 for shift in (16, 8, 0)] for v in values]
        else:
            assert kind == 'done'
    assert len(cases) == 240 and inputs == 128
    assert all(set(c) == {'key', 'binary', 'clear', 'cached'} for c in cases)
    return cases, inputs


def analyze(native):
    cases, inputs = decode(native)
    scores = []
    intermediate = []
    for c in cases:
        i, width, mode, source_width, requested_scale, requested_inner, outer, scale, inner, bmin, bmax, painted = c['key']
        values = list(map(number, c['binary']))
        a, tx, ia, itx, aa, ttx, fa, ftx, fia, fitx, ba, btx, reciprocal, divided, multiplied = values
        assert a == scale and float(format(tx, '.15g')) == inner and fa == a
        assert reciprocal == 1 / a and divided == tx / a and multiplied == tx * (1 / a)
        effective = round(inner * 4) / 4 + math.trunc(outer * 4) / 4
        positions = [x for x in range(1024) if effective + scale <= x and x + 1 <= effective + 15 * scale]
        # These sequences are global hypotheses, never selected from observed RGB.
        translations = {
            'baseline': effective,
            'inverse_roundtrip_child': round(ttx * 4) / 4 + math.trunc(outer * 4) / 4,
            'inverse_roundtrip_full': round((btx - outer) * 4) / 4 + math.trunc(outer * 4) / 4,
            'inverse_division_child': round((-itx / ia) * 4) / 4 + math.trunc(outer * 4) / 4,
            'inverse_division_full': round((-fitx / fia - outer) * 4) / 4 + math.trunc(outer * 4) / 4,
        }
        for name, translation in translations.items():
            origin = math.floor(translation)
            predicted = [[0, 0, 0] for _ in range(1024)]
            for x in positions:
                predicted[x] = sample(scale, translation - origin, x - origin, 16)
            scores.append({'case': int(i), 'model': name, **compare_samples(predicted, c['cached'], positions)})
        predicted = [[0, 0, 0] for _ in range(1024)]
        for x in positions:
            predicted[x] = sample(scale, effective, x, 16)
        scores.append({'case': int(i), 'model': 'uncached', **compare_samples(predicted, c['clear'], positions)})
        intermediate.append({'case': int(i), 'key': c['key'], 'binary': c['binary'], 'hex': [v.hex() for v in values],
                             'translations': translations, 'child_roundtrip_equal': tx == ttx, 'full_roundtrip_equal': ftx == btx})
    return {'input_exact': inputs, 'cases': intermediate, 'models': scores, 'candidate_admitted': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    for name in sorted({r['model'] for r in result['models']}):
        rows = [r for r in result['models'] if r['model'] == name]
        print(name, sum(r['exact'] for r in rows), sum(r['samples'] for r in rows))
