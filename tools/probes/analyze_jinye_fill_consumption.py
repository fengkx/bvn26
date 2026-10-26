"""Compare fixed compound-fill consumption orders against independent translation controls."""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path

from tools.probes.analyze_jinye_deep_gradients import deep_points
from tools.probes.analyze_jinye_affine_initializers import fixed_rows
from tools.probes.analyze_jinye_nearest_origin import compare_nearest
from tools.probes.analyze_jinye_translation_controls import models_for
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_fill_translation_controls import decode
from tools.probes.decode_jinye_sampling_modes import decode as decode_old


def combined_translation_model(direct, draw):
    matrix = list(direct)
    # This is a global transfer hypothesis, not an inferred native pipeline.
    # Preserve the independently constrained draw-offset consumption separately.
    matrix[4:] = [Fraction(round((translation-Fraction(offset))*4), 4)
                   + Fraction(math.trunc(Fraction(offset)*4), 4)
                   for translation, offset in zip(matrix[4:], draw[4:])]
    return fixed_rows(matrix, 'minimum')


def common_geometry(point_sets):
    if not point_sets:
        raise ValueError('No geometry controls')
    result = set(point_sets[0])
    for points in point_sets[1:]:
        result.intersection_update(points)
    return sorted(result, key=lambda p: (p[1], p[0]))


def native_delta(pixels, baseline, points, size):
    assert len(pixels) == len(baseline) == size[0]*size[1]
    histograms = [Counter() for _ in range(4)]
    failures = []
    for x, y in points:
        actual, old = pixels[y*size[0]+x], baseline[y*size[0]+x]
        for histogram, a, b in zip(histograms, actual, old):
            histogram[a-b] += 1
        if actual != old:
            failures.append([x, y, actual, old])
    return {'samples': len(points), 'exact': len(points)-len(failures),
            'max_channel_delta': [max(map(abs, h), default=0) for h in histograms],
            'signed_rgba_delta_histograms': [dict(sorted(h.items())) for h in histograms], 'failures': failures}


def draw_consumption_pairs(cases):
    groups = defaultdict(list)
    for case in cases:
        control = case['draw_control']
        if control is None:
            continue
        axis = control['axis']
        value = Fraction(str(case['native_matrix_readback'][17+axis]))
        groups[case['baseline_id'], case['cached'], axis, math.trunc(value*4)].append(case)
    results = []
    for key, members in groups.items():
        for a, b in itertools.combinations(members, 2):
            assert [r[:2] for r in a['codes']] == [r[:2] for r in b['codes']]
            failures = [[*ra[:2], ra[2], rb[2]] for ra, rb in zip(a['codes'], b['codes']) if ra[2] != rb[2]]
            results.append({'baseline_id': key[0], 'cached': key[1], 'axis': key[2],
                            'toward_zero_quarter_units': key[3], 'case_a': a['case'], 'case_b': b['case'],
                            'samples': len(a['codes']), 'exact': len(a['codes'])-len(failures), 'failures': failures})
    return {'pairs': results, 'pair_count': len(results),
            'changed_pairs': sum(bool(r['failures']) for r in results),
            'samples': sum(r['samples'] for r in results), 'exact': sum(r['exact'] for r in results)}


def collapsed_fill_pairs(cases):
    groups = defaultdict(list)
    for case in cases:
        if case['draw_variant'] != 0:
            continue
        fixed = tuple(tuple(row) for row in case['fixed_coordinate_rows']['combined_fill_child_then_draw_quarters/minimum'])
        groups[case['baseline_id'], case['cached'], fixed].append(case)
    pairs = []
    for (baseline, cached, fixed), members in groups.items():
        for a, b in itertools.combinations(members, 2):
            assert [r[:2] for r in a['codes']] == [r[:2] for r in b['codes']]
            failures = [[*ra[:2], ra[2], rb[2]] for ra, rb in zip(a['codes'], b['codes']) if ra[2] != rb[2]]
            pairs.append({'baseline_id': baseline, 'cached': cached, 'case_a': a['case'], 'case_b': b['case'],
                          'computed_fixed_rows': fixed, 'samples': len(a['codes']),
                          'exact': len(a['codes'])-len(failures), 'failures': failures})
    return {'pairs': pairs, 'pair_count': len(pairs), 'changed_pairs': sum(bool(p['failures']) for p in pairs),
            'samples': sum(p['samples'] for p in pairs), 'exact': sum(p['exact'] for p in pairs)}


def analyze(native):
    fixture, sources, captures, matrices = decode(native)
    old_fixture, old_sources, old_captures, old_matrices = decode_old(ROOT/'evidence/importer-loud-fail/r232/native')
    assert sources == [old_sources[0]]*13 and old_sources[0] == old_sources[1]
    size = tuple(fixture['size'])
    by_capture = {(c['source_case'], c['cached']): c for c in captures}
    baseline_specs = {s['baseline_id']: s for s in fixture['cases'] if s['fill_variant'] == 0 and s['draw_variant'] == 0}
    assert len(baseline_specs) == 4
    by_matrix = {int(r['values'][0]): r['values'] for r in matrices}
    old_matrix = {(r['mode'], int(r['values'][0])): r['values'] for r in old_matrices}
    old_capture = {(c['mode'], c['source_case'], c['cached'], c['clip_id']): c for c in old_captures}
    prepared = {}
    group_geometry = {key: [] for key in baseline_specs}
    for spec in fixture['cases']:
        original = next(s for s in fixture['source_graph']['shapes'] if s['id'] == spec['shape'])
        shape = dict(original, bitmap_matrix=spec['fill_matrix'])
        models, direct, polygon = models_for(spec, shape)
        models['combined_fill_child_then_draw_quarters/minimum'] = combined_translation_model(direct, spec['draw'])
        points = deep_points(tuple(polygon), size, 2)
        prepared[spec['id']] = models, points
        group_geometry[spec['baseline_id']].append(points)
    groups = {key: common_geometry(values) for key, values in group_geometry.items()}
    full = [(x, y) for y in range(size[1]) for x in range(size[0])]
    baselines = []
    for base_id, spec in baseline_specs.items():
        old = old_fixture['cases'][base_id]
        assert all(spec[k] == old[k] for k in ('shape', 'matrix', 'outer', 'draw', 'fill', 'mask'))
        assert by_matrix[spec['id']][1:19] == old_matrix[67, base_id][1:19]
        for cached in (False, True):
            baselines.append({'baseline_id': base_id, 'cached': cached,
                              **native_delta(by_capture[spec['id'], cached]['pixels'], old_capture[67, base_id, cached, 0]['pixels'], full, size)})
    results = []
    for spec in fixture['cases']:
        models, original_points = prepared[spec['id']]
        points = groups[spec['baseline_id']]
        for cached in (False, True):
            capture = by_capture[spec['id'], cached]
            base = by_capture[baseline_specs[spec['baseline_id']]['id'], cached]
            results.append({'case': spec['id'], 'baseline_id': spec['baseline_id'], 'shape': spec['shape'],
                            'scale': spec['draw'][0], 'cached': cached, 'fill_variant': spec['fill_variant'],
                            'fill_axis': spec['fill_axis'], 'fill_delta': spec['fill_delta'],
                            'draw_variant': spec['draw_variant'], 'draw_control': spec['draw_control'],
                            'parsed_fill_matrix': spec['fill_matrix'], 'native_matrix_readback': by_matrix[spec['id']],
                            'bounds': capture['bounds'], 'original_deep_samples': len(original_points),
                            'fixed_coordinate_rows': models,
                            'native_vs_baseline': native_delta(capture['pixels'], base['pixels'], points, size),
                            **compare_nearest(capture['pixels'], points, models, size)})
    totals = {model: {'samples': sum(r['samples'] for r in results), 'exact': sum(r['models'][model]['exact'] for r in results),
                      'max_channel_delta': [max(r['models'][model]['max_channel_delta'][k] for r in results) for k in range(4)]}
              for model in results[0]['models']}
    retained = {}
    for round_number in (229, 231, 232):
        path = ROOT/f'evidence/importer-loud-fail/r{round_number}/analysis.json'
        if not path.exists():
            path = path.with_suffix('.json.gz')
        retained[str(round_number)] = {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'cases': results, 'totals': totals, 'baselines': baselines,
            'same_consumed_draw_native_pairs': draw_consumption_pairs(results),
            'collapsed_combined_fill_native_pairs': collapsed_fill_pairs(results),
            'baseline_pixels': sum(r['samples'] for r in baselines), 'baseline_pixels_exact': sum(r['exact'] for r in baselines),
            'common_geometry': {str(k): v for k, v in groups.items()},
            'nearest_samples': sum(r['samples'] for r in results), 'nearest_texel_compatible': sum(r['texel_compatible'] for r in results),
            'source_readback_pixels_exact': sum(map(len, sources)), 'matrix_readbacks_exact': len(matrices),
            'native_fixture_sha256': hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest(),
            'retained': retained, 'fill_translation_provenance': 'parsed source tag bits, not AVM property readback',
            'new_model': 'source fill and child translations share quarter consumption before separately consumed draw translation',
            'new_model_independently_admitted': False, 'all_historical_nearest_controls_retested': False,
            'coordinate_fitted': False, 'geometry_selection_uses_native_pixels': False,
            'admission_suite_reduced': False, 'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('cases', 'baselines', 'common_geometry')}, indent=2))
