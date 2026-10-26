"""Intersect independently captured signed controls with every old CXFORM bound."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_cxform_brackets import (
    EVIDENCE, old_samples, read_adjacent, read_native as read_brackets, read_offset_controls,
    read_rejected, truncate_offsets,
)
from tools.probes.analyze_cxform_multiplier import (
    previous_report, quantize_multipliers, read_native as read_fine, read_signed,
)
from tools.probes.analyze_cxform_intervals import (
    channel, coefficient_measurements, f32, float_bits,
)
from tools.probes.analyze_cxform_rejected import measurements, rgb, score_sequence
from tools.probes.cxform_control_analysis import intersect
from tools.probes.cxform_signed_bounds import constraints, interval


def prior():
    previous_report()
    root = EVIDENCE/'r47'
    raw = (root/'analysis.json.gz').read_bytes()
    provenance = json.loads((root/'provenance.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=provenance['output_sha256']['analysis.json.gz']:
        raise ValueError('Pinned r47 evidence changed')
    return json.loads(gzip.decompress(raw))['quantized_multiplier_candidate']


def controls():
    rejected,_ = read_rejected(EVIDENCE/'r44/native')
    adjacent,_ = read_adjacent(EVIDENCE/'r45/native')
    brackets,_,_,_ = read_brackets(EVIDENCE/'r46/native')
    offsets,_ = read_offset_controls(EVIDENCE/'r46/offset')
    fine,_,_,_ = read_fine(EVIDENCE/'r47/native')
    previous = quantize_multipliers(truncate_offsets(list(old_samples())+list(rgb(rejected,'r44'))+
                list(rgb(adjacent,'r45'))+list(rgb(brackets,'r46_brackets'))+
                list(rgb(offsets,'r46_offset'))+list(rgb(fine,'r47_fine'))))
    signed = quantize_multipliers(truncate_offsets(list(rgb(read_signed(EVIDENCE/'r47/signed'),'signed'))))
    if (len(previous),len(signed))!=(1284192,18720):
        raise ValueError('Old or signed controls omitted')
    return previous,signed


def analyze():
    old = prior()
    previous,signed = controls()
    measured = coefficient_measurements(EVIDENCE/'r41')
    normal = measurements(EVIDENCE/'r44')
    candidates = {name:{a:v[name] for a,v in measured.items()} for name in measured[1]}
    for mode,table in normal.items():
        candidates['factorized_'+mode] = {a:f32(table[a][1]*table[1][0]) for a in table}
    reports = {}
    for space in ('unit','normalized','byte'):
        for order in ('alpha_first','opacity_first','joint'):
            key = space+'/'+order
            report = {}
            for group,added in (('green_intervals',[v for v in signed if v[0][-1]==1]),
                                ('combined_intervals',signed)):
                if group=='combined_intervals' and order!='alpha_first':
                    continue
                bounds = intersect(old['models'][key][group],constraints(added,space,order),'r47_adjusted')
                report[group] = bounds
                report['empty_'+group] = [a for a,v in bounds.items() if v['low_bits']>v['high_bits']]
                report['tightened_'+group] = [a for a,v in bounds.items()
                    if a not in old['models'][key][group] or
                    (v['low_bits'],v['high_bits'])!=(old['models'][key][group][a]['low_bits'],old['models'][key][group][a]['high_bits'])]
                fits = {}
                for name,values in candidates.items():
                    outside = []
                    for a,b in bounds.items():
                        coefficient = values[int(a)]
                        if space!='unit':
                            coefficient = f32(coefficient*255)
                        if not b['low_bits']<=float_bits(coefficient)<=b['high_bits']:
                            outside.append(int(a))
                    fits[name] = {'inside':len(bounds)-len(outside),'alphas':len(bounds),'outside':outside}
                report['membership_'+group] = fits
            if order=='alpha_first':
                report['total_constraints'] = len(previous)+len(signed)
            reports[key] = report
    scores = {}
    for mode,table in normal.items():
        for order in ('alpha_first','opacity_first','joint'):
            scores[mode+'/'+order] = {'old':score_sequence(previous,table,order),
                                    'signed':score_sequence(signed,table,order)}
    discriminator = []
    args = (25,49,-129,128,100)
    for space in ('unit','normalized','byte'):
        low,high = interval(args,space,'alpha_first',12)
        bounds = reports[space+'/alpha_first']['combined_intervals']['49']
        candidates_at_site = {}
        for name,values in candidates.items():
            coefficient = values[49]
            if space!='unit':
                coefficient = f32(coefficient*255)
            candidates_at_site[name] = {'coefficient_bits':float_bits(coefficient),
                                       'native':12,'actual':channel(args,coefficient,space,'alpha_first')}
        discriminator.append({'space':space,'args':list(args),'native':12,'signed_low_bits':low,
                              'signed_high_bits':high,'intersection_low_bits':bounds['low_bits'],
                              'intersection_high_bits':bounds['high_bits'],'constructions':candidates_at_site})
    return {'old_constraints':len(previous),'signed_constraints':len(signed),
            'signed_positive_channels':sum(args[2]>0 for _,args,_ in signed),
            'signed_zero_channels':sum(args[2]==0 for _,args,_ in signed),
            'signed_negative_channels':sum(args[2]<0 for _,args,_ in signed),
            'models':reports,'direct_sequences':scores,'alpha49_discriminator':discriminator,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze()
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    for key,v in report['models'].items():
        print(key,'empty',v['empty_green_intervals'],v.get('empty_combined_intervals'),
              'tightened',v.get('tightened_combined_intervals'),
              {n:m['inside'] for n,m in v.get('membership_combined_intervals',{}).items()})
    print('discriminator',report['alpha49_discriminator'])
    raise SystemExit(1)
