"""Gate authored-factorization comparisons on independent raw-tag baseline parity."""
import argparse
from fractions import Fraction
import hashlib
import gzip
import itertools
import json
from pathlib import Path

from tools.probes.analyze_jinye_factorization import compare_black_boundaries, compare_boundaries, effective_geometry, require_equivalent, summarize
from tools.probes.analyze_jinye_smooth_leaf import compose
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_source_factorization import decode, recover_linear_property
from tools.probes.jinye_source_factorization_tags import parse as parse_shape


def recover_matrix(actual, expected):
    if len(actual) != 6 or len(expected) != 6:
        raise ValueError('Expected affine matrix readback')
    result = []
    for index, (observed, declared) in enumerate(zip(actual, expected)):
        if index < 4:
            recovered = recover_linear_property(observed, declared)
            result.append(Fraction(recovered))
        else:
            if observed != declared:
                raise ValueError('Native translation property differs')
            value = Fraction(str(observed))
            if (value*20).denominator != 1:
                raise ValueError('Translation is not an exact authored twip')
            result.append(value)
    return result


def raw_geometry(parsed):
    style = parsed['styles'][1]
    assert style['bitmap'] == 55 and style['type'] == 67
    fill = [Fraction(v, 65536*20) for v in style['linear_fixed']]
    fill += [Fraction(v, 20) for v in style['translation_twips']]
    mask = [tuple(Fraction(v, 20) for v in point) for point in parsed['mask_twips']]
    return fill, mask


def baseline_gate(pairs):
    return bool(pairs) and all(p['full']['exact'] == p['full']['samples']
                               and p['black_composition']['full']['exact'] == p['black_composition']['full']['samples'] for p in pairs)


def pair_result(a, b, polygon, size):
    return {'bounds_a': a['bounds'], 'bounds_b': b['bounds'],
            'black_composition': compare_black_boundaries(a['black'], b['black'], polygon, size),
            **compare_boundaries(a['pixels'], b['pixels'], polygon, size)}


def analyze(native):
    fixture, source, captures, matrices = decode(native)
    assert source == [[2*x, 6*y, 73, 255] for y in range(40) for x in range(92)]
    size = tuple(fixture['size'])
    assert size == (256, 256)
    by_capture = {(c['source_case'], c['cached']): c for c in captures}
    by_matrix = {int(row[0]): row for row in matrices}
    log = native/'native.log'
    text = log.read_text() if log.exists() else gzip.decompress(log.with_suffix('.log.gz').read_bytes()).decode()
    matrix_events = [line.split('|')[7].split(',') for line in text.splitlines()
                     if line.startswith('AIREF|') and line.split('|')[6] == 'matrix']
    printed_matrices = {int(values[0]): values for values in matrix_events}
    assert len(printed_matrices) == len(matrices)
    assert all(list(map(float, printed_matrices[cid])) == values for cid, values in by_matrix.items())
    geometry, groups, proofs = {}, {}, []
    for spec in fixture['cases']:
        shape = next(s for s in fixture['shapes'] if s['parsed']['shape'] == spec['shape'])
        parsed = parse_shape(bytes.fromhex(shape['raw_tag_hex']))
        assert parsed == shape['parsed']
        fill, mask = raw_geometry(parsed)
        actual = by_matrix[spec['id']]
        child = recover_matrix(actual[1:7], spec['matrix'])
        outer = recover_matrix(actual[7:13], spec['outer'])
        draw = recover_matrix(actual[13:19], spec['draw'])
        effective = effective_geometry(fill, compose(outer, child), draw, mask)
        expected = ([Fraction(v) for v in spec['expected_total_rational']],
                    [tuple(Fraction(v) for v in p) for p in spec['expected_stage_mask_rational']])
        require_equivalent(effective, expected)
        assert all(0 < x < size[0] and 0 < y < size[1] for x, y in effective[1])
        geometry[spec['id']] = effective
        proofs.append({'case': spec['id'], 'raw_shape_sha256': shape['raw_tag_sha256'], 'native_readbacks': actual, 'original_native_property_text': printed_matrices[spec['id']],
                       'recovered_child_matrix': list(map(str, child)), 'effective_matrix': list(map(str, effective[0])),
                       'stage_mask': [list(map(str, p)) for p in effective[1]]})
        for cached in (False, True):
            groups.setdefault((spec['source_shape'], spec['draw'][0], cached), []).append(spec)
    baselines, factors = [], []
    for (source_shape, scale, cached), cases in groups.items():
        by_factor = {c['factor_id']: c for c in cases}
        assert set(by_factor) == {-1, 0, 1, 2, 3, 4}
        original, identity = by_factor[-1], by_factor[0]
        require_equivalent(geometry[original['id']], geometry[identity['id']])
        baselines.append({'source_shape': source_shape, 'scale': scale, 'cached': cached,
                          'original_case': original['id'], 'identity_case': identity['id'],
                          **pair_result(by_capture[original['id'], cached], by_capture[identity['id'], cached], geometry[original['id']][1], size)})
        for a, b in itertools.combinations([by_factor[i] for i in range(5)], 2):
            require_equivalent(geometry[a['id']], geometry[b['id']])
            factors.append({'source_shape': source_shape, 'scale': scale, 'cached': cached,
                            'case_a': a['id'], 'case_b': b['id'], 'factor_a': a['factor_id'], 'factor_b': b['factor_id'],
                            **pair_result(by_capture[a['id'], cached], by_capture[b['id'], cached], geometry[a['id']][1], size)})
    cache_pairs = []
    for spec in fixture['cases']:
        cache_pairs.append({'case': spec['id'], 'source_shape': spec['source_shape'], 'scale': spec['draw'][0], 'factor_id': spec['factor_id'],
                            **pair_result(by_capture[spec['id'], False], by_capture[spec['id'], True], geometry[spec['id']][1], size)})
    retained = {}
    for r in (232, 233, 234, 235):
        path = ROOT/f'evidence/importer-loud-fail/r{r}/analysis.json'
        if not path.exists():
            path = path.with_suffix('.json.gz')
        retained[str(r)] = {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'baseline_pairs': baselines, 'factorization_pairs': factors, 'cache_pairs': cache_pairs, 'geometry_proofs': proofs,
            'totals': {name: {'raw': summarize(pairs), 'black': summarize([p['black_composition'] for p in pairs])}
                       for name, pairs in (('baseline', baselines), ('factorization', factors), ('cache', cache_pairs))},
            'factorization_groups': [dict(source_shape=shape, scale=scale, cached=cached,
                                         raw=summarize([p for p in factors if (p['source_shape'], p['scale'], p['cached']) == (shape, scale, cached)]),
                                         black=summarize([p['black_composition'] for p in factors if (p['source_shape'], p['scale'], p['cached']) == (shape, scale, cached)]))
                                     for shape, scale, cached in sorted(groups)],
            'factorization_deep_code_samples': sum(p['deep_code_samples'] for p in factors),
            'factorization_deep_code_compatible': sum(p['deep_code_compatible'] for p in factors),
            'baseline_reencoding_gate_passed': baseline_gate(baselines),
            'factorization_measurements_interpretable': baseline_gate(baselines),
            'source_readback_pixels_exact': len(source), 'native_matrix_readbacks': len(matrices),
            'retained': retained, 'native_fixture_sha256': hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest(),
            'raw_plane': 'native getPixel32 RGBA; black composition independently compared',
            'linear_property_recovery': 'exact declared float32 recovered after 15-significant-digit half-up serialization and float32 roundtrip checks',
            'full_matrix_and_stage_mask_equivalence_exact': True, 'whole_authored_masks_within_target': True,
            'coordinate_model_tested': False, 'native_output_selected_geometry': False,
            'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('baseline_pairs', 'factorization_pairs', 'cache_pairs', 'geometry_proofs')}, indent=2))
    if not result['baseline_reencoding_gate_passed']:
        raise SystemExit(1)
