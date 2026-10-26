"""Independent adjacent-byte/alpha controls at fixed native CXFORM sites."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_cxform_alpha import capture_rows
from tools.probes.analyze_cxform_intervals import (
    coefficient_measurements, constraints, f32, float_bits,
)
from tools.probes.analyze_cxform_rejected import (
    EVIDENCE, ORDERS, distinguishing_sequences, measurements, merged, old_samples,
    prior, read_native as read_rejected, rgb, score_sequence,
)
from tools.probes.nested_composition import rgba
from tools.probes.run_nested_filters import unpack

SITES = ((49,13,2049,-896,67),(51,0,2048,-895,100),(204,9,1024,-385,100))


def previous_report():
    prior()
    root = EVIDENCE/'r44'
    raw = (root/'analysis.json.gz').read_bytes()
    provenance = json.loads((root/'provenance.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=provenance['output_sha256']['analysis.json.gz']:
        raise ValueError('Pinned r44 bounds changed')
    return json.loads(gzip.decompress(raw))


def read_native(directory):
    identities = []
    for site,(a,x,m,d,op) in enumerate(SITES):
        for da in range(-4,5):
            for dg in range(-8,9):
                identities.append([len(identities),site,a+da,dg,m,d,op])
    samples = []
    targets = []
    for row in capture_rows(directory,identities):
        i,site,a,dg,m,d,op = row[:7]
        for x in range(32):
            p,n = unpack(row[7+x*4:11+x*4])
            g = 120+x%16+(dg if x==SITES[site][1] else 0)
            if p!=rgba((117<<16)|(g<<8)|240,a):
                raise ValueError('Adjacent-site source readback changed')
            if n[3]!=a*(op*256//100)//256:
                raise ValueError('Adjacent-site alpha changed')
            numerator = p[1]*m*255+d*a*256
            clipped = not 0<numerator<a*256*255
            samples.append((i,x,p,n,m,d,op))
            if x==SITES[site][1]:
                targets.append({'key':[i,x],'site':site,'alpha':a,'delta_green':dg,
                                'requested_green':g,'source':p,'native':n,'clipped':clipped})
    return samples,targets


def analyze(root):
    old = previous_report()
    rows,targets = read_native(root/'native')
    rejected,_ = read_rejected(EVIDENCE/'r44/native')
    baseline = {(p[3],x,m,d,op):(p,n) for _,x,p,n,m,d,op in rejected}
    centered = {v['key'][0] for v in targets if v['alpha']==SITES[v['site']][0] and v['delta_green']==0}
    retained = [v for v in rows if v[0] in centered]
    if any(baseline[p[3],x,m,d,op]!=(p,n) for _,x,p,n,m,d,op in retained):
        raise ValueError('Centered r44 row changed')
    added = list(rgb(rows,'adjacent'))
    green = [v for v in added if v[0][-1]==1]
    measured = coefficient_measurements(EVIDENCE/'r41')
    normal = measurements(EVIDENCE/'r44')
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
                bounds = merged(old['models'][key][group],constraints(samples,space,order))
                for value in bounds.values():
                    for field in ('lower_witness','upper_witness'):
                        if value[field] and value[field]['key'][0]=='r43':
                            value[field]['key'][0] = 'r44'
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
    previous = list(old_samples())+list(rgb(rejected,'r44'))
    if len(previous)!=1057824:
        raise ValueError('Old controls omitted')
    sequences = {}
    target_keys = {tuple(v['key']) for v in targets}
    target_samples = [v for v in green if tuple(v[0][1:3]) in target_keys]
    target_scores = {}
    for mode,table in normal.items():
        for order in ORDERS:
            sequences[mode+'/'+order] = {'old':score_sequence(previous,table,order),
                                       'new':score_sequence(added,table,order)}
            target_scores[mode+'/'+order] = score_sequence(target_samples,table,order)
    return {'pixels':len(rows),'target_pixels':len(targets),'targets':targets,
            'centered_exact':len(retained),'models':reports,'direct_sequences':sequences,
            'target_sequences':target_scores,
            'normalization_discriminators':distinguishing_sequences(sequences),
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze(args.root)
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    print('pixels',report['pixels'],'targets',report['target_pixels'],'centered',report['centered_exact'])
    for key,v in report['models'].items():
        print(key,'empty',v['empty_green_intervals'],v.get('empty_combined_intervals'),
              {n:m['inside'] for n,m in v.get('membership_combined_intervals',{}).items()})
    for key,v in report['direct_sequences'].items():
        print(key,{n:{k:q for k,q in m.items() if k!='failures'} for n,m in v.items()})
    print('discriminators',{k:v['differing_channels'] for k,v in report['normalization_discriminators'].items()})
    raise SystemExit(1)
