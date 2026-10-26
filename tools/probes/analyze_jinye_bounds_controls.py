"""Compare native ShapeBounds-only controls without inferring cache allocation."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_jinye_factorization import effective_geometry, require_equivalent, summarize
from tools.probes.analyze_jinye_source_factorization import baseline_gate, pair_result, raw_geometry, recover_matrix
from tools.probes.analyze_jinye_smooth_leaf import compose
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_bounds_controls import decode
from tools.probes.decode_jinye_source_factorization import decode as decode_prior


def require_outward_patch(patch):
    before, after = patch['before'], patch['after']
    side = patch['side']
    expected = list(before)
    if side is not None:
        expected[side] += (-1 if side in (0, 2) else 1)*patch['amount_twips']
    if after != expected or not set(patch['changed_bits']) <= set(patch['allowed_changed_bits']):
        raise ValueError('Bounds patch changes something other than the declared outward side')


def aggregate(pairs):
    return {'raw': summarize(pairs), 'black': summarize([p['black_composition'] for p in pairs])}


def analyze(native, prior):
    fixture, sources, captures, matrices = decode(native)
    old_fixture, old_source, old_captures, _ = decode_prior(prior)
    assert all(source == old_source for source in sources)
    assert fixture['size'] == old_fixture['size'] == [256, 256]
    size = tuple(fixture['size'])
    by_capture = {(c['source_case'], c['cached']): c for c in captures}
    old_capture = {(c['source_case'], c['cached']): c for c in old_captures}
    by_matrix = {int(row[0]): row for row in matrices}
    geometries, proofs = {}, []
    for spec in fixture['cases']:
        require_outward_patch(spec['bounds_patch'])
        shape = next(s for s in fixture['shapes'] if s['source_shape'] == spec['source_shape'])
        fill, mask = raw_geometry(shape['parsed'])
        row = by_matrix[spec['id']]
        child = recover_matrix(row[1:7], spec['matrix'])
        outer = recover_matrix(row[7:13], spec['outer'])
        draw = recover_matrix(row[13:19], spec['draw'])
        geometry = effective_geometry(fill, compose(outer, child), draw, mask)
        expected = ([Fraction(v) for v in spec['expected_total_rational']],
                    [tuple(Fraction(v) for v in p) for p in spec['expected_stage_mask_rational']])
        require_equivalent(geometry, expected)
        assert all(0 < x < size[0] and 0 < y < size[1] for x, y in geometry[1])
        geometries[spec['id']] = geometry
        proofs.append({'case': spec['id'], 'bounds_patch': spec['bounds_patch'],
                       'raw_tag_sha256': spec['raw_tag_sha256'], 'native_property_readbacks': row,
                       'effective_matrix': list(map(str, geometry[0])),
                       'stage_mask': [list(map(str, p)) for p in geometry[1]]})
    baselines, bounds_pairs, cache_pairs = [], [], []
    for spec in fixture['cases']:
        base = next(s for s in fixture['cases'] if s['source_shape'] == spec['source_shape'] and s['variant'] == 0)
        require_equivalent(geometries[spec['id']], geometries[base['id']])
        polygon = geometries[spec['id']][1]
        for cached in (False, True):
            current = by_capture[spec['id'], cached]
            metadata = {'case': spec['id'], 'source_shape': spec['source_shape'], 'cached': cached,
                        'variant': spec['variant'], 'side': spec['bounds_patch']['side'],
                        'amount_twips': spec['bounds_patch']['amount_twips']}
            if spec['variant'] == 0:
                old_spec = old_fixture['cases'][spec['baseline_case']]
                assert old_spec['factor_id'] == -1 and old_spec['source_shape'] == spec['source_shape']
                assert old_spec['expected_total_rational'] == spec['expected_total_rational']
                assert old_spec['expected_stage_mask_rational'] == spec['expected_stage_mask_rational']
                baselines.append({**metadata, 'prior_case': spec['baseline_case'],
                                  **pair_result(old_capture[spec['baseline_case'], cached], current, polygon, size)})
            else:
                bounds_pairs.append({**metadata, **pair_result(by_capture[base['id'], cached], current, polygon, size)})
        cache_pairs.append({'case': spec['id'], 'source_shape': spec['source_shape'], 'variant': spec['variant'],
                            **pair_result(by_capture[spec['id'], False], by_capture[spec['id'], True], polygon, size)})
    retained = {}
    for round_id in (232, 233, 234, 235, 236):
        path = ROOT/f'evidence/importer-loud-fail/r{round_id}/analysis.json'
        if not path.exists():
            path = path.with_suffix('.json.gz')
        retained[str(round_id)] = {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'baseline_pairs': baselines, 'bounds_pairs': bounds_pairs, 'cache_pairs': cache_pairs,
            'geometry_proofs': proofs, 'totals': {name: aggregate(pairs) for name, pairs in
                                               (('baseline', baselines), ('bounds', bounds_pairs), ('cache', cache_pairs))},
            'groups': [{'source_shape': shape, 'cached': cached,
                        **aggregate([p for p in bounds_pairs if p['source_shape'] == shape and p['cached'] == cached])}
                       for shape in (56, 57) for cached in (False, True)],
            'baseline_gate_passed': baseline_gate(baselines),
            'bounds_measurements_interpretable': baseline_gate(baselines),
            'source_readback_pixels_exact': sum(map(len, sources)), 'native_matrix_readbacks': len(matrices),
            'retained': retained, 'native_fixture_sha256': hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest(),
            'raw_plane': 'native getPixel32 RGBA; black composition independently compared',
            'full_matrix_and_mask_equivalence_exact': True, 'whole_authored_mask_within_target': True,
            'get_bounds_identified_as_cache_allocation': False, 'coordinate_model_tested': False,
            'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--prior-native', type=Path, default=ROOT/'evidence/importer-loud-fail/r236/native')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native, args.prior_native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps({key: result[key] for key in ('totals', 'groups', 'baseline_gate_passed')}, indent=2))
    if not result['baseline_gate_passed']:
        raise SystemExit(1)
