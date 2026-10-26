"""Fine multiplier controls with explicit properties and fixed source bytes."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from tools.probes.analyze_cxform_alpha import capture_rows
from tools.probes.analyze_cxform_brackets import (
    EVIDENCE, SITES, prior, read_adjacent, read_native as read_brackets,
    read_offset_controls, read_rejected, old_samples, sources, truncate_offsets,
)
from tools.probes.analyze_cxform_intervals import coefficient_measurements
from tools.probes.analyze_cxform_rejected import measurements, rgb, score_sequence
from tools.probes.nested_composition import rgba
from tools.probes.cxform_control_analysis import evaluate
from tools.probes.run_nested_filters import unpack

DELTAS = (-256,-255,-129,-128,-127,-1,0,1,127,128,129,255,256)


def previous_report():
    prior()
    root = EVIDENCE/'r46'
    raw = (root/'analysis.json.gz').read_bytes()
    provenance = json.loads((root/'provenance.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=provenance['output_sha256']['analysis.json.gz']:
        raise ValueError('Pinned r46 evidence changed')
    return json.loads(gzip.decompress(raw))['truncated_offset_candidate']


def read_native(directory):
    adjacent,_ = read_adjacent(EVIDENCE/'r45/native')
    reference = {(i,x):(p,n) for i,x,p,n,m,d,op in adjacent}
    identities = []
    for v in sources():
        site,a,dg,ref = v['site'],v['alpha'],v['delta_green'],v['key'][0]
        _,_,m,d,op = SITES[site]
        for delta in DELTAS:
            identities.append([len(identities),ref,site,a,dg,m*256+delta,d,op,m*256+delta])
    samples,targets,clipping = [],[],[]
    centered = 0
    for row in capture_rows(directory,identities):
        i,ref,site,a,dg,m65536,d,op,property_value = row[:9]
        for x in range(32):
            p,n = unpack(row[9+x*4:13+x*4])
            expected,baseline = reference[ref,x]
            if p!=expected:
                raise ValueError('Fixed multiplier source changed')
            if n[3]!=a*(op*256//100)//256:
                raise ValueError('Fine multiplier alpha changed')
            if m65536==SITES[site][2]*256:
                if n!=baseline:
                    raise ValueError('Center multiplier changed')
                centered += 1
            numerator = p[1]*m65536*255+d*a*65536
            if not 0<numerator<a*65536*255:
                clipping.append([i,x])
            samples.append((i,x,p,n,m65536/256,d,op))
            if x==SITES[site][1]:
                targets.append({'key':[i,x],'reference':[ref,x],'site':site,'source':p,'native':n,
                                'multiplier_65536':m65536,'offset':d,'opacity':op})
    return samples,targets,clipping,centered


def anchor_comparisons(rows):
    # Native-only comparisons reject coarse consumption hypotheses. Agreement
    # alone does not identify storage precision or a hardware implementation.
    outputs = {(i,x):n for i,x,p,n,m,d,op in rows}
    reports = {}
    for mode in ('floor_8_8','nearest_8_8','toward_zero_8_8'):
        failures = []
        for i,x,p,n,m,d,op in rows:
            start = i//len(DELTAS)*len(DELTAS)
            anchor = int(m) if mode=='toward_zero_8_8' else (math.floor(m) if mode=='floor_8_8' else math.floor(m+0.5))
            center = rows[start*32][4]-DELTAS[0]/256
            delta = int((anchor-center)*256)
            reference = outputs[start+DELTAS.index(delta),x]
            if n!=reference:
                failures.append({'key':[i,x],'native':n,'anchor_native':reference,'anchor_delta':delta})
        reports[mode] = {'pixels':len(rows),'exact':len(rows)-len(failures),'failures':failures}
    return reports


def read_signed(directory):
    identities = []
    for a in (49,51,135,204,255):
        for center in (-128,0,128):
            for delta in DELTAS:
                identities.append([len(identities),a,center,center*256+delta,center*256+delta])
    samples = []
    for row in capture_rows(directory,identities):
        i,a,center,m,property_value = row[:5]
        for x in range(32):
            p,n = unpack(row[5+x*4:9+x*4])
            if p!=rgba(0x7580f0,a) or n[3]!=a:
                raise ValueError('Signed multiplier source/alpha changed')
            numerator = p[1]*m*255+128*a*65536
            if not 0<numerator<a*65536*255:
                raise ValueError('Signed multiplier reaches clipping')
            samples.append((i,x,p,n,m/256,128,100))
    return samples


def quantize_multipliers(samples):
    return [(key,(args[0],args[1],int(args[2]),args[3],args[4]),target) for key,args,target in samples]


def analyze(root):
    old = previous_report()
    rows,targets,clipping,centered = read_native(root/'native')
    rejected,_ = read_rejected(EVIDENCE/'r44/native')
    adjacent,_ = read_adjacent(EVIDENCE/'r45/native')
    brackets,_,_,_ = read_brackets(EVIDENCE/'r46/native')
    offsets,_ = read_offset_controls(EVIDENCE/'r46/offset')
    previous = truncate_offsets(list(old_samples())+list(rgb(rejected,'r44'))+
                                list(rgb(adjacent,'r45'))+list(rgb(brackets,'r46_brackets'))+
                                list(rgb(offsets,'r46_offset')))
    if len(previous)!=1224288:
        raise ValueError('Old controls omitted')
    added = list(rgb(rows,'fine'))
    keys = {tuple(v['key']) for v in targets}
    target_samples = [v for v in added if v[0][-1]==1 and tuple(v[0][1:3]) in keys]
    result = evaluate(old,added,previous,target_samples,
                      coefficient_measurements(EVIDENCE/'r41'),measurements(EVIDENCE/'r44'),'r46_adjusted')
    adjusted = evaluate(old,quantize_multipliers(added),quantize_multipliers(previous),
                        quantize_multipliers(target_samples),coefficient_measurements(EVIDENCE/'r41'),
                        measurements(EVIDENCE/'r44'),'r46_adjusted')
    signed = read_signed(root/'signed')
    signed_controls = list(rgb(signed,'signed'))
    signed_scores = {}
    # The interval solver assumes positive multipliers. Negative controls are
    # checked directly, never passed to its monotone-increasing binary search.
    for mode,table in measurements(EVIDENCE/'r44').items():
        for order in ('alpha_first','opacity_first','joint'):
            signed_scores[mode+'/'+order] = {'raw':score_sequence(signed_controls,table,order),
                'quantized':score_sequence(quantize_multipliers(signed_controls),table,order)}
    result['quantized_multiplier_candidate'] = adjusted
    result['signed_controls'] = {'pixels':len(signed),'anchor_comparisons':anchor_comparisons(signed),
                               'direct_sequences':signed_scores,'property_fraction_preserved':True}
    result.update(pixels=len(rows),target_pixels=len(targets),targets=targets,
                  sources=len(sources()),clipping=clipping,centered_exact=centered,
                  property_fraction_preserved=True,anchor_comparisons=anchor_comparisons(rows))
    return result


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze(args.root)
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    print({k:report[k] for k in ('pixels','target_pixels','sources','centered_exact')})
    print('clipping',len(report['clipping']))
    print('anchors',{k:v['exact'] for k,v in report['anchor_comparisons'].items()})
    for key,v in report['models'].items():
        print(key,'empty',v['empty_green_intervals'],v.get('empty_combined_intervals'),
              {n:m['inside'] for n,m in v.get('membership_combined_intervals',{}).items()})
    for key,v in report['direct_sequences'].items():
        print(key,{n:{k:q for k,q in m.items() if k!='failures'} for n,m in v.items()},
              'target',report['target_sequences'][key]['exact'])
    print('signed anchors',{k:v['exact'] for k,v in report['signed_controls']['anchor_comparisons'].items()})
    for key,v in report['quantized_multiplier_candidate']['models'].items():
        print('quantized',key,'empty',v['empty_green_intervals'],v.get('empty_combined_intervals'))
    print('quantized targets',{k:v['exact'] for k,v in report['quantized_multiplier_candidate']['target_sequences'].items()})
    raise SystemExit(1)
