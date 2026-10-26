"""Measure texel-code compatibility without fitting source coordinates."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_jinye_deep_gradients import deep_points
from tools.probes.analyze_jinye_translation_controls import models_for
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_tag_controls import decode as decode_old


def compatible_texel(pixel):
    if len(pixel) != 4:
        raise ValueError("Expected RGBA readback")
    r, g, b, a = pixel
    if a != 255 or b != 73 or r % 2 or g % 6 or not 0 <= r//2 < 92 or not 0 <= g//6 < 40:
        return None
    return [r//2, g//6]


def predict_nearest(rows, x, y):
    indices = [(a*x+b*y+t+offset)//65536 for a, b, t, offset in rows]
    ix, iy = max(0, min(91, indices[0])), max(0, min(39, indices[1]))
    return [2*ix, 6*iy, 73, 255]


def compare_smooth_channels(pixels, horizontal, vertical, size):
    if len(pixels) != len(horizontal) or len(pixels) != len(vertical) or len(pixels) != size[0]*size[1]:
        raise ValueError("Native image extent mismatch")
    failures = []
    for i, (p, h, v) in enumerate(zip(pixels, horizontal, vertical)):
        expected = [h[0], v[1], h[2], h[3]]
        if h[2:] != v[2:] or p != expected:
            failures.append([i % size[0], i//size[0], p, h, v])
    return {"samples": len(pixels), "exact": len(pixels)-len(failures), "failures": failures}


def compare_nearest(pixels, points, models, size):
    if len(pixels) != size[0]*size[1]:
        raise ValueError("Native image extent mismatch")
    codes = []
    incompatible = []
    for x, y in points:
        pixel = pixels[y*size[0]+x]
        code = compatible_texel(pixel)
        codes.append([x, y, pixel, code])
        if code is None:
            incompatible.append([x, y, pixel])
    scores = {}
    for model, rows in models.items():
        failures = []
        deltas = [Counter() for _ in range(4)]
        for x, y, pixel, _ in codes:
            expected = predict_nearest(rows, x, y)
            for hist, a, b in zip(deltas, expected, pixel):
                hist[a-b] += 1
            if expected != pixel:
                failures.append([x, y, expected, pixel])
        scores[model] = {"samples": len(points), "exact": len(points)-len(failures),
                         "max_channel_delta": [max(map(abs, h), default=0) for h in deltas],
                         "signed_rgba_delta_histograms": [dict(sorted(h.items())) for h in deltas], "failures": failures}
    return {"samples": len(points), "texel_compatible": len(points)-len(incompatible),
            "incompatible": incompatible, "codes": codes, "models": scores}


def analyze(native):
    from tools.probes.decode_jinye_sampling_modes import decode

    fixture, sources, captures, matrices = decode(native)
    old_fixture, old_sources, old_captures, old_matrices = decode_old(ROOT/"evidence/importer-loud-fail/r223/native")
    generated = [[2*x, 6*y, 73, 255] for y in range(40) for x in range(92)]
    assert sources == [generated, generated]
    size = tuple(fixture['size'])
    assert size == (96, 96)
    matrix_map = {(r['mode'], int(r['values'][0])): r['values'] for r in matrices}
    by_key = {(c['mode'], c['source_case'], c['cached'], c['clip_id']): c for c in captures}
    assert len(matrix_map) == len(matrices) and len(by_key) == len(captures)
    crosschecks = []
    results = []
    for spec in fixture['cases']:
        horizontal, vertical = [old_fixture['cases'][spec[key]] for key in ('base_h', 'base_v')]
        for old in (horizontal, vertical):
            assert all(spec[key] == old[key] for key in ('shape', 'matrix', 'outer', 'draw', 'fill', 'mask'))
        for mode in (65, 67):
            assert matrix_map[mode, spec['id']][1:19] == old_matrices[horizontal['id']][1:19]
        shape = next(s for s in fixture['source_graph']['shapes'] if s['id'] == spec['shape'])
        models, _, polygon = models_for(spec, shape)
        points = deep_points(tuple(polygon), size, 2)
        for cached in (False, True):
            smooth = by_key[65, spec['id'], cached, 0]
            old_h, old_v = [old_captures[old['id']*2+int(cached)]['pixels'] for old in (horizontal, vertical)]
            crosschecks.append({'case': spec['id'], 'shape': spec['shape'], 'scale': spec['draw'][0], 'cached': cached,
                                **compare_smooth_channels(smooth['pixels'], old_h, old_v, size)})
            for clip_id, clip in enumerate(fixture['clips']):
                selected = points if clip is None else [(x, y) for x, y in points
                                                       if clip[0] <= x < clip[0]+clip[2] and clip[1] <= y < clip[1]+clip[3]]
                capture = by_key[67, spec['id'], cached, clip_id]
                result = compare_nearest(capture['pixels'], selected, models, size)
                results.append({'case': spec['id'], 'shape': spec['shape'], 'scale': spec['draw'][0], 'cached': cached,
                                'clip_id': clip_id, 'clip': clip, 'bounds': capture['bounds'], **result})
    totals = {model: {'samples': sum(r['samples'] for r in results),
                      'exact': sum(r['models'][model]['exact'] for r in results),
                      'max_channel_delta': [max(r['models'][model]['max_channel_delta'][k] for r in results) for k in range(4)]}
              for model in results[0]['models']}
    prior_path = ROOT/'evidence/importer-loud-fail/r231/analysis.json'
    if not prior_path.exists():
        prior_path = prior_path.with_suffix('.json.gz')
    return {'cases': results, 'totals': totals, 'smooth_crosschecks': crosschecks,
            'smooth_full_pixels': sum(r['samples'] for r in crosschecks),
            'smooth_full_pixels_exact': sum(r['exact'] for r in crosschecks),
            'nearest_deep_samples': sum(r['samples'] for r in results),
            'nearest_texel_compatible': sum(r['texel_compatible'] for r in results),
            'source_readback_pixels_exact': 7360, 'matrix_readbacks_exact': len(matrices),
            'native_fixture_sha256': hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest(),
            'retained_r231_analysis_path': str(prior_path.relative_to(ROOT)),
            'retained_r231_analysis_sha256': hashlib.sha256(prior_path.read_bytes()).hexdigest(),
            'texel_codes_prove_internal_cache_sampling_origin': False,
            'nearest_primitive_transfer_to_compound_fill_proved': False,
            'incompatible_readbacks_excluded': False, 'geometry_selection_uses_native_pixels': False,
            'coordinate_fitted': False, 'admission_suite_reduced': False,
            'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('cases', 'smooth_crosschecks')}, indent=2))
