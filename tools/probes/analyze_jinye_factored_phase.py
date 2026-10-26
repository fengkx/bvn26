"""Test one globally defined phase projection without changing inverse coefficients."""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_jinye_deep_gradients import deep_points
from tools.probes.analyze_jinye_nearest_origin import compare_nearest
from tools.probes.analyze_jinye_smooth_leaf import invert, source_geometry
from tools.probes.analyze_jinye_translation_controls import models_for
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_sampling_modes import decode as decode_modes
from tools.probes.decode_jinye_fill_translation_controls import decode as decode_fill

IDENTITY = [1, 0, 0, 1, 0, 0]


def projected_phase(full_rows, display_rows, inverse_fill):
    a, b, c, d = inverse_fill[:4]
    offsets = [round(a*display_rows[0][3]+c*display_rows[1][3]),
               round(b*display_rows[0][3]+d*display_rows[1][3])]
    return tuple(tuple(row[:3])+(offset,) for row, offset in zip(full_rows, offsets))


def phase_models(spec, shape):
    full, _, polygon = models_for(spec, shape)
    identity_shape = dict(shape, bitmap_matrix={'scaleX': '20', 'scaleY': '20',
                                               'rotateSkew0': '0', 'rotateSkew1': '0',
                                               'translateX': '0', 'translateY': '0'})
    display, _, display_polygon = models_for(spec, identity_shape)
    assert polygon == display_polygon
    fill, _ = source_geometry({'matrix': IDENTITY, 'outer': IDENTITY, 'draw': IDENTITY}, shape)
    inverse_fill = invert(fill)
    result = {}
    for key, rows in full.items():
        if not key.endswith('/minimum'):
            continue
        result[key+'/full_phase'] = rows
        result[key+'/projected_display_phase'] = projected_phase(rows, display[key], inverse_fill)
        assert [r[:3] for r in result[key+'/projected_display_phase']] == [tuple(r[:3]) for r in rows]
    return result, polygon


def read_report(round_number):
    path = ROOT/f'evidence/importer-loud-fail/r{round_number}/analysis.json'
    if not path.exists():
        path = path.with_suffix('.json.gz')
    raw = path.read_bytes()
    report = json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)
    return report, {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(raw).hexdigest()}


def analyze(native_fill):
    old232, pin232 = read_report(232)
    old233, pin233 = read_report(233)
    results = {'r232': [], 'r233': []}
    fixture, _, captures, _ = decode_modes(ROOT/'evidence/importer-loud-fail/r232/native')
    for capture in captures:
        if capture['mode'] != 67:
            continue
        spec = fixture['cases'][capture['source_case']]
        shape = next(s for s in fixture['source_graph']['shapes'] if s['id'] == spec['shape'])
        models, polygon = phase_models(spec, shape)
        points = deep_points(tuple(polygon), (96, 96), 2)
        clip = capture['clip']
        if clip is not None:
            points = [(x, y) for x, y in points if clip[0] <= x < clip[0]+clip[2] and clip[1] <= y < clip[1]+clip[3]]
        previous = next(c for c in old232['cases'] if c['case'] == spec['id'] and c['cached'] == capture['cached'] and c['clip_id'] == capture['clip_id'])
        assert [list(p) for p in points] == [row[:2] for row in previous['codes']]
        results['r232'].append({'case': spec['id'], 'shape': spec['shape'], 'scale': spec['draw'][0],
                               'cached': capture['cached'], 'clip_id': capture['clip_id'], 'fixed_rows': models,
                               **compare_nearest(capture['pixels'], points, models, (96, 96))})
    fixture, _, captures, _ = decode_fill(native_fill)
    assert hashlib.sha256((native_fill/'fixture.json').read_bytes()).hexdigest() == old233['native_fixture_sha256']
    for capture in captures:
        spec = fixture['cases'][capture['source_case']]
        shape = dict(next(s for s in fixture['source_graph']['shapes'] if s['id'] == spec['shape']), bitmap_matrix=spec['fill_matrix'])
        models, _ = phase_models(spec, shape)
        points = old233['common_geometry'][str(spec['baseline_id'])]
        previous = next(c for c in old233['cases'] if c['case'] == spec['id'] and c['cached'] == capture['cached'])
        assert points == [row[:2] for row in previous['codes']]
        results['r233'].append({'case': spec['id'], 'shape': spec['shape'], 'scale': spec['draw'][0],
                               'cached': capture['cached'], 'fill_variant': spec['fill_variant'], 'draw_variant': spec['draw_variant'],
                               'fixed_rows': models, **compare_nearest(capture['pixels'], points, models, (96, 96))})
    for suite, old in (('r232', old232), ('r233', old233)):
        for case in results[suite]:
            previous = next(c for c in old['cases'] if c['case'] == case['case'] and c['cached'] == case['cached']
                            and (suite != 'r232' or c['clip_id'] == case['clip_id']))
            for name, score in case['models'].items():
                if name.endswith('/full_phase'):
                    assert json.loads(json.dumps(score)) == previous['models'][name.removesuffix('/full_phase')]
    totals = {}
    for suite, cases in results.items():
        totals[suite] = {model: {'samples': sum(c['samples'] for c in cases),
                                 'exact': sum(c['models'][model]['exact'] for c in cases),
                                 'max_channel_delta': [max(c['models'][model]['max_channel_delta'][k] for c in cases) for k in range(4)]}
                         for model in cases[0]['models']}
    qualifying = [model for model in totals['r232'] if model.endswith('/projected_display_phase')
                  and all(totals[suite][model]['exact'] == totals[suite][model]['samples'] for suite in totals)]
    return {'cases': results, 'totals': totals, 'retained': {'232': pin232, '233': pin233},
            'unchanged_full_phase_scores_and_all_failures_exact': True, 'qualifying_model_names': qualifying,
            'phase_definition': 'ties-even projection of quantized display-only minimum-norm phase through exact inverse-fill linear matrix',
            'inverse_coefficients_and_translation_unchanged': True,
            'source_output_selected_phase': False, 'coordinate_fitted': False,
            'old_nearest_and_smooth_advance_allowed': bool(qualifying),
            'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-fill', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native_fill)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps(result['totals'], indent=2))
