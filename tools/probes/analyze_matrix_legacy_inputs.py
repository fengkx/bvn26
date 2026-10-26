"""Preserve old vector outputs and test their newly observed unfiltered source bytes."""
import argparse
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.run_nested_filters import unpack
from tools.probes.matrix_packed_candidate import coefficients, pixel


def decode_scalar(native):
    rows = []
    original = events(ROOT/'evidence/importer-loud-fail/r11/pixels/color-arithmetic')
    fresh = events(native)
    assert [v for v in fresh if v[0] in ('sample', 'done')] == original
    for kind, value in fresh:
        values = value.split(',')
        if kind == 'input':
            assert len(values) == 5
            rows.append({'key': list(map(int, values[:3])), 'input': unpack(list(map(int, values[3:])))[0]})
        elif kind == 'matrix':
            assert len(values) == 20 and 'matrix' not in rows[-1]
            rows[-1]['matrix'] = list(map(float, values))
        elif kind == 'sample':
            assert list(map(int, values[:3])) == rows[-1]['key']
            rows[-1]['native'] = unpack(list(map(int, values[3:])))[0]
        else:
            assert [kind, value] == ['done', 'ok']
    assert len(rows) == 24
    return rows


def decode_ramp(native):
    original = events(ROOT/'evidence/importer-loud-fail/r12/pixels/color-arithmetic-ramp')
    fresh = events(native)
    assert [v for v in fresh if v[0] in ('color', 'black', 'done')] == original
    rows = []
    for kind, value in fresh:
        values = value.split(',')
        if kind == 'matrix':
            assert len(values) == 20
            rows.append({'matrix': list(map(float, values))})
        elif kind != 'done':
            assert kind in ('input', 'inputBlack', 'color', 'black') and len(values) == 258
            row = rows[-1]
            key = list(map(int, values[:2]))
            assert row.get('key', key) == key and kind not in row
            row['key'] = key
            row[kind] = list(map(int, values[2:]))
        else:
            assert value == 'ok'
    assert len(rows) == 8
    for row in rows:
        row['source'] = unpack([v for pair in zip(row['input'], row['inputBlack']) for v in pair])
        row['native'] = unpack([v for pair in zip(row['color'], row['black']) for v in pair])
    return rows


def analyze(scalar, ramp):
    scalar_rows = decode_scalar(scalar)
    ramp_rows = decode_ramp(ramp)
    results = {}
    for name, rows in [('scalar', scalar_rows), ('ramp', ramp_rows)]:
        result = {'samples': 0, 'exact': 0, 'failures': [], 'max_channel_delta': 0}
        for row in rows:
            matrix = coefficients(row['matrix'])
            sources = [row['input']] if name == 'scalar' else row['source']
            targets = [row['native']] if name == 'scalar' else row['native']
            for x, (source, target) in enumerate(zip(sources, targets)):
                # Original64px vector interior is in the paired prefix; the2px
                # vector's separately rounded+expanded3px cache is a remainder.
                mode = 'remainder' if name == 'ramp' else ('opaque_pair' if source[3] == 255 else 'alpha_pair')
                actual = pixel(source, matrix, mode)
                result['samples'] += 1
                result['exact'] += actual == target
                result['max_channel_delta'] = max(result['max_channel_delta'], max(abs(a-b) for a,b in zip(actual,target)))
                if actual != target:
                    result['failures'].append({'key': row['key'], 'x': x, 'input': source, 'actual': actual, 'native': target})
        results[name] = result
    return {'original_outputs_unchanged': True, 'scalar_rows': scalar_rows, 'ramp_rows': ramp_rows,
            'comparisons': results, 'production_admitted': False, 'gpu_binding_completed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scalar', type=Path, required=True)
    parser.add_argument('--ramp', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.scalar, args.ramp)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print({k: {a:b for a,b in v.items() if a != 'failures'} for k,v in result['comparisons'].items()})
