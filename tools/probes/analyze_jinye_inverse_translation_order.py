"""Reject fixed inverse-translation operation orders without choosing a phase."""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jinye_smooth_leaf import compose, source_geometry
from tools.probes.analyze_jinye_affine_initializers import fixed_rows
from tools.probes.analyze_jinye_phase_constraints import cell_bounds, intersect, finalize
from tools.probes.analyze_jinye_nearest_origin import compatible_texel

MODEL = 'scaled_child_then_draw_quarters/minimum'


def round_fixed(value):
    return math.floor(value+Fraction(1, 2))


def quantized_translation(a, b, tx, ty, order):
    if order == 'quantize_coefficients_then_dot_then_round':
        return round_fixed(-a*tx-b*ty)
    if order == 'quantize_coefficients_then_round_products_then_sum':
        return round_fixed(-a*tx)+round_fixed(-b*ty)
    raise ValueError('Unknown independent operation sequence')


def consumed_matrix(spec, shape):
    child = compose(list(map(Fraction, spec['outer'])), list(map(Fraction, spec['matrix'])))
    draw = list(map(Fraction, spec['draw']))
    transformed = compose(draw[:4]+[Fraction(0), Fraction(0)], child)
    transformed[4:] = [Fraction(round(v*4), 4)+Fraction(math.trunc(t*4), 4) for v,t in zip(transformed[4:],draw[4:])]
    return source_geometry(dict(spec, matrix=transformed, outer=[1,0,0,1,0,0], draw=[1,0,0,1,0,0]), shape)[0]


def analyze():
    report_path = ROOT/'evidence/importer-loud-fail/r233/analysis.json.gz'
    fixture_path = ROOT/'evidence/importer-loud-fail/r233/native/fixture.json'
    data = json.loads(gzip.decompress(report_path.read_bytes()))
    fixture = json.loads(fixture_path.read_text())
    orders = ('retained_exact_inverse_then_quantize', 'quantize_coefficients_then_dot_then_round',
              'quantize_coefficients_then_round_products_then_sum')
    groups = {}
    scores = {order: {'samples': 0, 'exact': 0, 'failures': 0, 'first_failure': None} for order in orders}
    translations = []
    for case in data['cases']:
        spec = fixture['cases'][case['case']]
        shape = dict(next(s for s in fixture['source_graph']['shapes'] if s['id'] == spec['shape']), bitmap_matrix=spec['fill_matrix'])
        matrix = consumed_matrix(spec, shape)
        rows = fixed_rows(matrix, 'minimum')
        assert [list(row) for row in rows] == case['fixed_coordinate_rows'][MODEL]
        for order in orders:
            adjusted = [(*row[:2], row[2] if order == orders[0] else quantized_translation(*row[:2], *matrix[4:], order), row[3]) for row in rows]
            translations.append({'case':case['case'],'cached':case['cached'],'order':order,'old_t':[r[2] for r in rows],'new_t':[r[2] for r in adjusted]})
            for axis, (a,b,t,phase) in enumerate(adjusted):
                key = case['baseline_id'],case['cached'],axis,order
                group = groups.setdefault(key, {'baseline_id':case['baseline_id'],'shape':case['shape'],'scale':case['scale'],
                    'cached':case['cached'],'axis':axis,'order':order,'constraints':0,'lower':None,'upper':None,
                    'lower_witness':None,'upper_witness':None,'predeclared_phases':{phase}})
                for x,y,pixel,cell in case['codes']:
                    if compatible_texel(pixel) != cell:
                        raise ValueError('Incompatible retained native code')
                    base = a*x+b*y+t
                    intersect(group, cell_bounds(base,cell[axis],(92,40)[axis]),
                              {'case':case['case'],'coordinate':[x,y],'cell':cell,'base':base,'translation':t})
            score = scores[order]
            for x,y,pixel,cell in case['codes']:
                predicted = [max(0,min(limit-1,(a*x+b*y+t+phase)//65536)) for (a,b,t,phase),limit in zip(adjusted,(92,40))]
                score['samples'] += 1
                score['exact'] += predicted == cell
                if predicted != cell:
                    score['failures'] += 1
                    if score['first_failure'] is None:
                        score['first_failure'] = {'case':case['case'],'cached':case['cached'],'coordinate':[x,y],'predicted_cell':predicted,'native_cell':cell}
    result = [finalize(group) for group in groups.values()]
    return {'scores':scores,'constraints':result,'translations':translations,
            'summary':{order:{'feasible_row_groups':sum(g['constant_phase_feasible'] for g in result if g['order']==order),
                              'row_groups':sum(g['order']==order for g in result)} for order in orders},
            'inputs':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (report_path,fixture_path)],
            'old_axis_controls_advanced':False,'reason':'Every alternative is rejected on the retained compound-fill gate before axis admission.',
            'phase_chosen_from_interval':False,'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result=analyze();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'scores':result['scores'],'summary':result['summary']},indent=2))
