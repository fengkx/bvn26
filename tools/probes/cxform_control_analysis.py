"""Intersect fixed native controls without supplying coefficients to a renderer."""
import copy

from tools.probes.analyze_cxform_intervals import constraints, f32, float_bits
from tools.probes.analyze_cxform_rejected import ORDERS, distinguishing_sequences, score_sequence


def intersect(old, added, prior_label):
    result = copy.deepcopy(old)
    for value in result.values():
        for field in ('lower_witness','upper_witness'):
            if value[field]:
                value[field]['key'] = [prior_label,*value[field]['key']]
    for a,value in added.items():
        current = result.setdefault(str(a),copy.deepcopy(value))
        if value['low_bits']>current['low_bits']:
            current['low_bits'],current['lower_witness'] = value['low_bits'],value['lower_witness']
        if value['high_bits']<current['high_bits']:
            current['high_bits'],current['upper_witness'] = value['high_bits'],value['upper_witness']
    return result


def evaluate(old, added, previous, targets, measured, normal, prior_label):
    green = [v for v in added if v[0][-1]==1]
    candidates = {name:{a:v[name] for a,v in measured.items()} for name in measured[1]}
    for mode,table in normal.items():
        candidates['factorized_'+mode] = {a:f32(table[a][1]*table[1][0]) for a in table}
    reports = {}
    for space in ('unit','normalized','byte'):
        for order in ORDERS:
            key = space+'/'+order
            report = {}
            for group,samples in (('green_intervals',green),('combined_intervals',added)):
                if group=='combined_intervals' and order!='alpha_first':
                    continue
                bounds = intersect(old['models'][key][group],constraints(samples,space,order),prior_label)
                report[group] = bounds
                report['empty_'+group] = [a for a,v in bounds.items() if v['low_bits']>v['high_bits']]
                fits = {}
                for name,values in candidates.items():
                    outside = []
                    for a,b in bounds.items():
                        value = values[int(a)]
                        if space!='unit':
                            value = f32(value*255)
                        if not b['low_bits']<=float_bits(value)<=b['high_bits']:
                            outside.append(int(a))
                    fits[name] = {'inside':len(bounds)-len(outside),'alphas':len(bounds),'outside':outside}
                report['membership_'+group] = fits
            if order=='alpha_first':
                report['total_constraints'] = old['models'][key]['total_constraints']+len(added)
            reports[key] = report
    sequences,target_scores = {},{}
    for mode,table in normal.items():
        for order in ORDERS:
            key = mode+'/'+order
            sequences[key] = {'old':score_sequence(previous,table,order),
                              'new':score_sequence(added,table,order)}
            target_scores[key] = score_sequence(targets,table,order)
    return {'models':reports,'direct_sequences':sequences,'target_sequences':target_scores,
            'normalization_discriminators':distinguishing_sequences(sequences),
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}
