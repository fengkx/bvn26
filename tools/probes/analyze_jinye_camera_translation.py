"""Compare native camera shifts using only declared integer coordinate mappings."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_jinye_clip_controls import compare_at
from tools.probes.analyze_jinye_deep_gradients import deep_points
from tools.probes.analyze_jinye_factorization import effective_geometry, require_equivalent, summarize
from tools.probes.analyze_jinye_source_factorization import baseline_gate, pair_result, raw_geometry, recover_matrix
from tools.probes.analyze_jinye_smooth_leaf import compose
from tools.probes.build_bound_bitmap_component import ROOT


def translated_comparison(left, right, polygon, size, offset):
    dx, dy = offset
    if type(dx) is not int or type(dy) is not int:
        raise ValueError('Camera correspondence requires declared integer offsets')
    width, height = size
    assert len(left['pixels']) == len(right['pixels']) == len(left['black']) == len(right['black']) == width*height
    overlap = {(x, y) for y in range(height) for x in range(width) if 0 <= x+dx < width and 0 <= y+dy < height}
    target_overlap = {(x+dx, y+dy) for x, y in overlap}
    all_points = {(x, y) for y in range(height) for x in range(width)}
    deep = set(deep_points(tuple(polygon), tuple(size), 2))
    assert deep <= overlap
    planes, outside = {}, {}
    for plane, empty in (('pixels', [0, 0, 0, 0]), ('black', [0, 0, 0, 255])):
        aligned = [empty]*len(right[plane])
        for x, y in overlap:
            aligned[y*width+x] = right[plane][(y+dy)*width+x+dx]
        planes[plane] = {name: compare_at(left[plane], aligned, points, size) for name, points in
                         (('full', overlap), ('deep', deep), ('outside_deep', overlap-deep))}
        outside[plane] = {}
        for side, capture, points in (('baseline', left, all_points-overlap), ('shifted', right, all_points-target_overlap)):
            failures = [[x, y, capture[plane][y*width+x]] for x, y in sorted(points) if capture[plane][y*width+x] != empty]
            outside[plane][side] = {'samples': len(points), 'exact': len(points)-len(failures), 'failures': failures}
    return {**planes['pixels'], 'black_composition': planes['black'], 'outside_overlap': outside,
            'outside_overlap_clear': all(v['samples'] == v['exact'] for plane in outside.values() for v in plane.values()),
            'bounds_baseline': left['bounds'], 'bounds_shifted': right['bounds']}


def analyze(native, prior):
    from tools.probes.decode_jinye_camera_controls import decode
    from tools.probes.decode_jinye_signed_factorization import decode as decode_prior
    fixture, source, captures, matrices = decode(native)
    old_fixture, old_source, old_captures, _ = decode_prior(prior)
    assert source == old_source
    assert fixture['size'] == old_fixture['size'] == [256, 256]
    size = tuple(fixture['size'])
    current = {(c['source_case'], c['cached']): c for c in captures}
    old = {(c['source_case'], c['cached']): c for c in old_captures}
    rows = {int(row[0]): row for row in matrices}
    geometry, proofs = {}, []
    for spec in fixture['cases']:
        base = old_fixture['cases'][spec['baseline_case']]
        assert spec['matrix'] == base['matrix'] and spec['outer'] == base['outer']
        dx, dy = spec['camera_offset']
        assert all(type(v) is int for v in (dx, dy))
        assert spec['draw'] == base['draw'][:4]+[base['draw'][4]+dx, base['draw'][5]+dy]
        shape = next(s for s in fixture['shapes'] if s['parsed']['shape'] == spec['shape'])
        old_shape = next(s for s in old_fixture['shapes'] if s['parsed']['shape'] == base['shape'])
        assert shape == old_shape
        fill, mask = raw_geometry(shape['parsed'])
        row = rows[spec['id']]
        child = recover_matrix(row[1:7], spec['matrix'])
        outer = recover_matrix(row[7:13], spec['outer'])
        draw = recover_matrix(row[13:19], spec['draw'])
        result = effective_geometry(fill, compose(outer, child), draw, mask)
        original = ([Fraction(v) for v in base['expected_total_rational']],
                    [tuple(Fraction(v) for v in p) for p in base['expected_stage_mask_rational']])
        translated = (original[0][:4]+[original[0][4]+dx, original[0][5]+dy],
                      [(x+dx, y+dy) for x, y in original[1]])
        require_equivalent(result, translated)
        assert all(0 < x < size[0] and 0 < y < size[1] for x, y in result[1])
        geometry[spec['id']] = original
        proofs.append({'case': spec['id'], 'native_properties': row, 'raw_shape_sha256': shape['raw_tag_sha256'],
                       'effective_matrix': list(map(str, result[0])), 'stage_mask': [list(map(str, p)) for p in result[1]]})
    baselines, translated_pairs = [], []
    for spec in fixture['cases']:
        base = next(c for c in fixture['cases'] if c['baseline_case'] == spec['baseline_case'] and c['camera_offset'] == [0, 0])
        for cached in (False, True):
            metadata = {'case': spec['id'], 'baseline_case': spec['baseline_case'], 'source_shape': spec['source_shape'],
                        'factor_id': spec['factor_id'], 'cached': cached, 'camera_offset': spec['camera_offset']}
            if spec['camera_offset'] == [0, 0]:
                baselines.append({**metadata, **pair_result(old[spec['baseline_case'], cached], current[spec['id'], cached], geometry[spec['id']][1], size)})
            else:
                translated_pairs.append({**metadata, **translated_comparison(current[base['id'], cached], current[spec['id'], cached], geometry[spec['id']][1], size, spec['camera_offset'])})
    retained = {}
    for round_id in range(232, 240):
        path = ROOT/f'evidence/importer-loud-fail/r{round_id}/analysis.json'
        if not path.exists():
            path = path.with_suffix('.json.gz')
        retained[str(round_id)] = {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'baseline_pairs': baselines, 'translation_pairs': translated_pairs, 'geometry_proofs': proofs,
            'totals': {name: {'raw': summarize(pairs), 'black': summarize([p['black_composition'] for p in pairs])}
                       for name, pairs in (('baseline', baselines), ('translation', translated_pairs))},
            'baseline_gate_passed': baseline_gate(baselines),
            'outside_overlap_clear': all(p['outside_overlap_clear'] for p in translated_pairs),
            'source_readback_pixels_exact': len(source), 'native_matrix_readbacks': len(matrices),
            'retained': retained, 'native_fixture_sha256': hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest(),
            'coordinate_model_tested': False, 'cache_allocation_origin_proved': False,
            'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--prior-native', type=Path, default=ROOT/'evidence/importer-loud-fail/r239/native')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native, args.prior_native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps({key: result[key] for key in ('totals', 'baseline_gate_passed', 'outside_overlap_clear')}, indent=2))
    if not result['baseline_gate_passed'] or not result['outside_overlap_clear']:
        raise SystemExit(1)
