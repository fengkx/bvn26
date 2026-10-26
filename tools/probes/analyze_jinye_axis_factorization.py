"""Native-only exact axis factorization comparisons with raw baseline gates."""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path

from tools.probes.analyze_jinye_factorization import effective_geometry, require_equivalent, summarize
from tools.probes.analyze_jinye_source_factorization import baseline_gate, pair_result, raw_geometry, recover_matrix
from tools.probes.analyze_jinye_smooth_leaf import compose
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_axis_factorization import decode
from tools.probes.jinye_source_factorization_tags import parse as parse_shape


def factor_groups(cases, expected_factors=(-1, 0, 1, 2, 3)):
    groups = {}
    for case in cases:
        key = (case['source_shape'], case['draw'][0])
        group = groups.setdefault(key, {})
        if case['factor_id'] in group:
            raise ValueError('Duplicate factor in geometry group')
        group[case['factor_id']] = case
    if not groups or any(set(group) != set(expected_factors) for group in groups.values()):
        raise ValueError('Each group requires untouched raw, identity and every declared factor')
    return groups


def aggregate(pairs):
    return {'raw': summarize(pairs), 'black': summarize([p['black_composition'] for p in pairs])}


def analyze(native, *, decoder=decode, expected_factors=(-1, 0, 1, 2, 3), retained_rounds=(232, 233, 234, 235, 236, 237)):
    fixture, source, captures, matrices = decoder(native)
    assert source == [[2*x, 6*y, 73, 255] for y in range(40) for x in range(92)]
    size = tuple(fixture['size'])
    assert size == (256, 256)
    by_capture = {(c['source_case'], c['cached']): c for c in captures}
    by_matrix = {int(row[0]): row for row in matrices}
    geometries, proofs = {}, []
    for spec in fixture['cases']:
        shape = next(s for s in fixture['shapes'] if s['parsed']['shape'] == spec['shape'])
        parsed = parse_shape(bytes.fromhex(shape['raw_tag_hex']))
        assert parsed == shape['parsed']
        fill, mask = raw_geometry(parsed)
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
        proofs.append({'case': spec['id'], 'raw_tag_sha256': shape['raw_tag_sha256'], 'native_readbacks': row,
                       'recovered_child_matrix': list(map(str, child)), 'effective_matrix': list(map(str, geometry[0])),
                       'stage_mask': [list(map(str, p)) for p in geometry[1]]})
    baselines, factors, cache_pairs = [], [], []
    for (shape, scale), cases in factor_groups(fixture['cases'], expected_factors).items():
        for cached in (False, True):
            for a, b in [(-1, 0), *itertools.combinations([factor for factor in expected_factors if factor >= 0], 2)]:
                first, second = cases[a], cases[b]
                require_equivalent(geometries[first['id']], geometries[second['id']])
                pair = {'source_shape': shape, 'scale': scale, 'cached': cached, 'factor_a': a, 'factor_b': b,
                        'case_a': first['id'], 'case_b': second['id'],
                        **pair_result(by_capture[first['id'], cached], by_capture[second['id'], cached], geometries[first['id']][1], size)}
                (baselines if a == -1 else factors).append(pair)
    for spec in fixture['cases']:
        cache_pairs.append({'case': spec['id'], 'source_shape': spec['source_shape'], 'factor_id': spec['factor_id'],
                            **pair_result(by_capture[spec['id'], False], by_capture[spec['id'], True], geometries[spec['id']][1], size)})
    retained = {}
    for round_id in retained_rounds:
        path = ROOT/f'evidence/importer-loud-fail/r{round_id}/analysis.json'
        if not path.exists():
            path = path.with_suffix('.json.gz')
        retained[str(round_id)] = {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'baseline_pairs': baselines, 'factorization_pairs': factors, 'cache_pairs': cache_pairs,
            'geometry_proofs': proofs, 'totals': {name: aggregate(pairs) for name, pairs in
                                               (('baseline', baselines), ('factorization', factors), ('cache', cache_pairs))},
            'groups': [{'source_shape': shape, 'cached': cached,
                        **aggregate([p for p in factors if p['source_shape'] == shape and p['cached'] == cached])}
                       for shape in (56, 57) for cached in (False, True)],
            'baseline_gate_passed': baseline_gate(baselines), 'factorization_measurements_interpretable': baseline_gate(baselines),
            'source_readback_pixels_exact': len(source), 'native_matrix_readbacks': len(matrices),
            'retained': retained, 'native_fixture_sha256': hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest(),
            'raw_plane': 'native getPixel32 RGBA; black composition independently compared',
            'full_matrix_and_stage_mask_equivalence_exact': True, 'whole_authored_masks_within_target': True,
            'coordinate_model_tested': False, 'cache_allocation_origin_proved': False,
            'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps({key: result[key] for key in ('totals', 'groups', 'baseline_gate_passed')}, indent=2))
    if not result['baseline_gate_passed']:
        raise SystemExit(1)
