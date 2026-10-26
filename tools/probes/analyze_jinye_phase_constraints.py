"""Reject constant-phase explanations using exact native nearest-cell inequalities."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jinye_nearest_origin import compatible_texel


QUANTUM = 65536


def cell_bounds(base, cell, size):
    if not 0 <= cell < size:
        raise ValueError('Native cell outside source domain')
    lower = None if cell == 0 else cell*QUANTUM-base
    upper = None if cell == size-1 else (cell+1)*QUANTUM-1-base
    return lower, upper


def intersect(state, bounds, witness):
    lower, upper = bounds
    state['constraints'] += 1
    if lower is not None and (state['lower'] is None or lower > state['lower']):
        state['lower'], state['lower_witness'] = lower, witness
    if upper is not None and (state['upper'] is None or upper < state['upper']):
        state['upper'], state['upper_witness'] = upper, witness


def finalize(state):
    low, high = state['lower'], state['upper']
    state['constant_phase_feasible'] = low is None or high is None or low <= high
    state['predeclared_phase_results'] = [{'phase': phase, 'satisfies_all_constraints':
                                         (low is None or phase >= low) and (high is None or phase <= high)}
                                        for phase in sorted(state.pop('predeclared_phases'))]
    return state


def analyze(path):
    data = json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())
    groups = {}
    for case in data['cases']:
        if case['incompatible']:
            raise ValueError(f"Incompatible native source codes at case {case['case']}")
        assert case['samples'] == len(case['codes']) == case['texel_compatible']
        for model, rows in case['fixed_coordinate_rows'].items():
            for axis, (a, b, t, phase) in enumerate(rows):
                key = (case['baseline_id'], case['cached'], model, axis)
                group = groups.setdefault(key, {'baseline_id': case['baseline_id'], 'shape': case['shape'],
                                                'scale': case['scale'], 'cached': case['cached'], 'model': model,
                                                'axis': axis, 'linear_coefficients': [a, b], 'constraints': 0,
                                                'lower': None, 'upper': None, 'lower_witness': None,
                                                'upper_witness': None, 'predeclared_phases': set(), 'cases': []})
                assert group['linear_coefficients'] == [a, b]
                group['predeclared_phases'].add(phase)
                group['cases'].append(case['case'])
                for x, y, pixel, decoded in case['codes']:
                    actual = compatible_texel(pixel)
                    if actual is None or actual != decoded:
                        raise ValueError('Native source code is incompatible or altered')
                    base = a*x+b*y+t
                    witness = {'case': case['case'], 'coordinate': [x, y], 'native_rgba': pixel,
                               'native_cell': decoded, 'fixed_base_without_phase': base,
                               'fixed_translation': t, 'fill_variant': case['fill_variant'],
                               'draw_variant': case['draw_variant']}
                    intersect(group, cell_bounds(base, actual[axis], (92, 40)[axis]), witness)
    results = [finalize(group) for group in groups.values()]
    return {'groups': results, 'group_count': len(results),
            'feasible_groups': sum(g['constant_phase_feasible'] for g in results),
            'empty_groups': sum(not g['constant_phase_feasible'] for g in results),
            'constraints': sum(g['constraints'] for g in results),
            'input_path': str(path.relative_to(ROOT)), 'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'all_retained_cases': len(data['cases']), 'all_retained_native_samples': sum(c['samples'] for c in data['cases']),
            'intervals_are_rejection_constraints_only': True, 'phase_chosen_from_interval': False,
            'coefficients_fitted': False, 'rendering_model_tested': False,
            'candidate_admitted': False, 'gpu_advance_allowed': False, 'production_admitted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=ROOT/'evidence/importer-loud-fail/r233/analysis.json.gz')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = analyze(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('group_count', 'feasible_groups', 'empty_groups', 'constraints')}))
