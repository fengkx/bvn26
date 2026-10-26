"""Compare exact matrix factorizations without assigning an internal sampling phase."""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path

from tools.probes.analyze_jinye_clip_controls import compare_at
from tools.probes.analyze_jinye_deep_gradients import deep_points
from tools.probes.analyze_jinye_nearest_origin import compatible_texel
from tools.probes.analyze_jinye_smooth_leaf import compose, transform
from tools.probes.build_bound_bitmap_component import ROOT


def fractions(values):
    return [Fraction(str(v)) for v in values]


def effective_geometry(fill, child, draw, mask):
    display = compose(fractions(draw), fractions(child))
    effective = compose(display, fractions(fill))
    polygon = [transform(display, fractions(point)) for point in mask]
    return effective, polygon


def require_equivalent(left, right):
    if left[0] != right[0]:
        raise ValueError('Actual bitmap-to-stage matrices differ')
    if left[1] != right[1]:
        raise ValueError('Actual stage masks differ')


def compare_boundaries(left, right, polygon, size):
    full = {(x, y) for y in range(size[1]) for x in range(size[0])}
    deep = set(deep_points(tuple(polygon), tuple(size), 2))
    incompatible = []
    for x, y in sorted(deep, key=lambda p: (p[1], p[0])):
        for side, pixels in (('left', left), ('right', right)):
            pixel = pixels[y*size[0]+x]
            if compatible_texel(pixel) is None:
                incompatible.append([x, y, side, pixel])
    return {'full': compare_at(left, right, full, size),
            'deep': compare_at(left, right, deep, size),
            'outside_deep': compare_at(left, right, full-deep, size),
            'deep_code_incompatible': incompatible,
            'deep_code_samples': len(deep)*2, 'deep_code_compatible': len(deep)*2-len(incompatible)}


def compare_black_boundaries(left, right, polygon, size):
    full = {(x, y) for y in range(size[1]) for x in range(size[0])}
    deep = set(deep_points(tuple(polygon), tuple(size), 2))
    return {'full': compare_at(left, right, full, size),
            'deep': compare_at(left, right, deep, size),
            'outside_deep': compare_at(left, right, full-deep, size)}


def summarize(pairs):
    return {boundary: {'comparisons': len(pairs),
                       'images_exact': sum(p[boundary]['samples'] == p[boundary]['exact'] for p in pairs),
                       'samples': sum(p[boundary]['samples'] for p in pairs),
                       'exact': sum(p[boundary]['exact'] for p in pairs),
                       'max_channel_delta': [max((p[boundary]['max_channel_delta'][k] for p in pairs), default=0) for k in range(4)]}
            for boundary in ('full', 'deep', 'outside_deep')}


def analyze(native):
    from tools.probes.decode_jinye_factorization_controls import decode
    from tools.probes.jinye_factorization_tags import parse_shape

    fixture, source, captures, matrices = decode(native)
    assert source == [[2*x, 6*y, 73, 255] for y in range(40) for x in range(92)]
    size = tuple(fixture['size'])
    assert size == (192, 192)
    by_matrix = {int(row[0]): row for row in matrices}
    by_capture = {(c['source_case'], c['cached']): c for c in captures}
    geometry = {}
    proofs = []
    groups = {}
    for spec in fixture['cases']:
        shape = next(s for s in fixture['shapes'] if s['parsed']['shape'] == spec['shape'])
        parsed = parse_shape(bytes.fromhex(shape['raw_tag_hex']))
        assert parsed == shape['parsed']
        actual = by_matrix[spec['id']]
        child, outer, draw = actual[1:7], actual[7:13], actual[13:19]
        combined_child = compose(fractions(outer), fractions(child))
        effective = effective_geometry(parsed['fill'], combined_child, draw, parsed['mask'])
        expected = (fractions(spec['expected_total']), [tuple(fractions(p)) for p in spec['expected_stage_mask']])
        require_equivalent(effective, expected)
        geometry[spec['id']] = effective
        proofs.append({'case': spec['id'], 'raw_shape_sha256': shape['raw_tag_sha256'], 'native_property_readbacks': actual,
                       'effective_matrix': list(map(str, effective[0])), 'stage_mask': [list(map(str, p)) for p in effective[1]]})
        for cached in (False, True):
            groups.setdefault((spec['display_id'], spec['draw'][0], cached), []).append(spec)
    pairs = []
    for (display, scale, cached), cases in groups.items():
        assert {c['factor_id'] for c in cases} == set(range(5))
        for a, b in itertools.combinations(cases, 2):
            require_equivalent(geometry[a['id']], geometry[b['id']])
            left, right = by_capture[a['id'], cached], by_capture[b['id'], cached]
            pairs.append({'display_id': display, 'scale': scale, 'cached': cached,
                          'case_a': a['id'], 'case_b': b['id'], 'factor_a': a['factor_id'], 'factor_b': b['factor_id'],
                          'bounds_a': left['bounds'], 'bounds_b': right['bounds'],
                          'black_composition': compare_black_boundaries(left['black'], right['black'], geometry[a['id']][1], size),
                          **compare_boundaries(left['pixels'], right['pixels'], geometry[a['id']][1], size)})
    cache_pairs = []
    for spec in fixture['cases']:
        left, right = by_capture[spec['id'], False], by_capture[spec['id'], True]
        cache_pairs.append({'case': spec['id'], 'display_id': spec['display_id'], 'scale': spec['draw'][0],
                            'factor_id': spec['factor_id'], 'uncached_bounds': left['bounds'], 'cached_bounds': right['bounds'],
                            'black_composition': compare_black_boundaries(left['black'], right['black'], geometry[spec['id']][1], size),
                            **compare_boundaries(left['pixels'], right['pixels'], geometry[spec['id']][1], size)})
    retained = {}
    for number in (232, 233, 234):
        path = ROOT/f'evidence/importer-loud-fail/r{number}/analysis.json'
        if not path.exists():
            path = path.with_suffix('.json.gz')
        retained[str(number)] = {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'factorization_pairs': pairs, 'cache_pairs': cache_pairs, 'geometry_proofs': proofs,
            'primary_comparison_plane': 'native raw getPixel32 RGBA; not inferred premultiplied bytes',
            'factorization_totals': summarize(pairs), 'cache_totals': summarize(cache_pairs),
            'black_composition_totals': {'factorization': summarize([p['black_composition'] for p in pairs]),
                                         'cache': summarize([p['black_composition'] for p in cache_pairs])},
            'source_readback_pixels_exact': len(source), 'matrix_readbacks_exact': len(matrices),
            'deep_code_samples': sum(p['deep_code_samples'] for p in pairs),
            'deep_code_compatible': sum(p['deep_code_compatible'] for p in pairs),
            'retained': retained, 'native_fixture_sha256': hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest(),
            'geometry_equivalence_exact': True, 'native_pixel_selected_geometry': False,
            'new_coordinate_model_tested': False, 'coordinate_fitted': False,
            'internal_sampling_origin_proved': False, 'general_factorization_invariance_proved': False,
            'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('factorization_pairs', 'cache_pairs', 'geometry_proofs')}, indent=2))
