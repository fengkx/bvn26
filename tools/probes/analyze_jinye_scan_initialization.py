"""Test fixed row/column initialization orders on retained native source cells."""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jinye_inverse_translation_order import consumed_matrix, round_fixed, MODEL
from tools.probes.analyze_jinye_affine_initializers import fixed_rows, inverse_rows
from tools.probes.analyze_jinye_phase_constraints import cell_bounds, intersect, finalize
from tools.probes.analyze_jinye_nearest_origin import compatible_texel

ORDERS = ('retained_quantized_steps', 'exact_row_start_quantized_x_step', 'exact_column_start_quantized_y_step')


def initialized_base(exact, quantized, x, y, order):
    ea, eb, et = exact
    a, b, t, _ = quantized
    if order == ORDERS[0]:
        return a*x+b*y+t
    if order == ORDERS[1]:
        return round_fixed((eb*y+et)*65536)+a*x
    if order == ORDERS[2]:
        return round_fixed((ea*x+et)*65536)+b*y
    raise ValueError('Unknown predeclared initialization order')


def analyze():
    report_path = ROOT/'evidence/importer-loud-fail/r233/analysis.json.gz'
    fixture_path = ROOT/'evidence/importer-loud-fail/r233/native/fixture.json'
    data = json.loads(gzip.decompress(report_path.read_bytes()))
    fixture = json.loads(fixture_path.read_text())
    assert len(data['cases']) == 2*len(fixture['cases']) == 200
    assert {(c['case'], c['cached']) for c in data['cases']} == {(c['id'], cached) for c in fixture['cases'] for cached in (False, True)}
    prepared = {}
    for spec in fixture['cases']:
        shape = dict(next(s for s in fixture['source_graph']['shapes'] if s['id'] == spec['shape']), bitmap_matrix=spec['fill_matrix'])
        matrix = consumed_matrix(spec, shape)
        prepared[spec['id']] = inverse_rows(matrix), fixed_rows(matrix, 'minimum')
    groups, cases = {}, []
    for case in data['cases']:
        assert not case['incompatible'] and case['samples'] == case['texel_compatible'] == len(case['codes'])
        exact, quantized = prepared[case['case']]
        assert [list(row) for row in quantized] == case['fixed_coordinate_rows'][MODEL]
        results = {}
        for order in ORDERS:
            failures = []
            states = []
            for axis, row in enumerate(quantized):
                key = case['baseline_id'], case['cached'], axis, order
                state = groups.setdefault(key, {'baseline_id':case['baseline_id'],'shape':case['shape'],'scale':case['scale'],
                    'cached':case['cached'],'axis':axis,'order':order,'constraints':0,'lower':None,'upper':None,
                    'lower_witness':None,'upper_witness':None,'predeclared_phases':{row[3]}, 'linear_coefficients':list(row[:2])})
                assert state['linear_coefficients'] == list(row[:2]) and state['predeclared_phases'] == {row[3]}
                states.append(state)
            for x,y,pixel,cell in case['codes']:
                if compatible_texel(pixel) != cell:
                    raise ValueError('Incompatible native source-cell code')
                predicted = []
                for axis, (ex, row, limit, state) in enumerate(zip(exact,quantized,(92,40),states)):
                    base = initialized_base(ex,row,x,y,order)
                    predicted.append(max(0,min(limit-1,(base+row[3])//65536)))
                    intersect(state,cell_bounds(base,cell[axis],limit),{'case':case['case'],'coordinate':[x,y],
                              'native_cell':cell,'fixed_base_without_phase':base})
                if predicted != cell:
                    failures.append([x,y,predicted,cell])
            results[order] = {'samples':len(case['codes']),'exact':len(case['codes'])-len(failures),'failures':failures}
        cases.append({'case':case['case'],'baseline_id':case['baseline_id'],'shape':case['shape'],'scale':case['scale'],
                      'cached':case['cached'],'exact_inverse_rows':[[str(v) for v in row] for row in exact],
                      'fixed_rows':quantized,'orders':results})
    constraints = [finalize(g) for g in groups.values()]
    totals = {order:{'samples':sum(c['orders'][order]['samples'] for c in cases),
                    'exact':sum(c['orders'][order]['exact'] for c in cases),
                    'feasible_phase_groups':sum(g['constant_phase_feasible'] for g in constraints if g['order']==order),
                    'phase_groups':sum(g['order']==order for g in constraints)} for order in ORDERS}
    assert totals[ORDERS[0]]['exact'] == data['totals'][MODEL]['exact']
    qualifiers = [order for order in ORDERS[1:] if totals[order]['samples']==totals[order]['exact']]
    return {'cases':cases,'constraints':constraints,'totals':totals,'qualifying_orders':qualifiers,
            'inputs':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (report_path,fixture_path)],
            'initialized_row_column_origin':0,'native_scan_origin_proved':False,
            'old_axis_retest_required':bool(qualifiers),'old_axis_retested':False,
            'phase_chosen_from_interval':False,'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=analyze();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps(result['totals'],indent=2))
