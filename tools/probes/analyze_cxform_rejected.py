"""Held-out amplified alphas and independently measured normalization sequences."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_cxform_alpha import ROOT, alpha_samples, capture_rows
from tools.probes.analyze_cxform_amplified import intersect, previous_report, read_samples
from tools.probes.analyze_cxform_identity import read_identity, read_stages, read_zero, stage_transform
from tools.probes.analyze_cxform_intervals import (
    channel, coefficient_measurements, constraints, f32, float_bits, from_bits, native_samples,
)
from tools.probes.nested_composition import rgba
from tools.probes.run_nested_filters import unpack

EVIDENCE = ROOT/'evidence/importer-loud-fail'
MODES = ('divide','multiply_rounded','multiply_estimated')
ORDERS = ('alpha_first','opacity_first','joint')


def prior():
    previous_report()
    root = EVIDENCE/'r43'
    provenance = json.loads((root/'provenance.json').read_text())
    raw = (root/'analysis.json.gz').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=provenance['output_sha256']['analysis.json.gz']:
        raise ValueError('Pinned r43 bounds changed')
    return json.loads(gzip.decompress(raw))


def alphas():
    old = prior()
    rejected = old['models']['unit/alpha_first']['membership']['estimate_quotient']['outside']
    return sorted(set(rejected)|{146,197,206,244})


def read_native(directory):
    identities = []
    for a in alphas():
        for gain in (2,4,8):
            for adjacent in (-1,0,1):
                for offset in (-1,0,1):
                    for op in (33,67,100):
                        identities.append([len(identities),a,gain*256+adjacent,-(gain-1)*128+offset,op])
    samples = []
    clipping = []
    for row in capture_rows(directory,identities):
        i,a,m,d,op = row[:5]
        for x in range(32):
            p,n = unpack(row[5+x*4:9+x*4])
            if p!=rgba((117<<16)|((120+x%16)<<8)|240,a):
                raise ValueError('Explicit amplified input changed')
            if n[3]!=a*(op*256//100)//256:
                raise ValueError('Amplified alpha changed')
            numerator = p[1]*m*255+d*a*256
            if not 0<numerator<a*256*255:
                clipping.append({'key':[i,x],'alpha':a,'source':p,'multiplier':m,'offset':d})
            samples.append((i,x,p,n,m,d,op))
    return samples,clipping


def rgb(rows, group):
    for i,x,p,n,m,d,op in rows:
        for ch,mul,offset in ((0,128,8),(1,m,d),(2,256,-4)):
            yield ([group,i,x,ch],(p[ch],p[3],mul,offset,op),n[ch])


def old_samples():
    yield from rgb(native_samples(EVIDENCE/'r41/native'),'r41')
    for name,ops in (('alpha',(25,50,100)),('opacity',(1,33,67,99))):
        for key,p,n,op in alpha_samples(EVIDENCE/'r40'/name,ops):
            if not p[3]:
                continue
            for ch,m,d in ((0,128,8),(1,192,0),(2,256,-4)):
                yield ([name,*key,ch],(p[ch],p[3],m,d,op),n[ch])
    yield from rgb(read_identity(EVIDENCE/'r42/native'),'identity')
    yield from rgb(read_zero(EVIDENCE/'r42/zero'),'zero')
    for i,stage,x,p,n,m,d,op in read_stages(EVIDENCE/'r42/stages'):
        mul,offset,actual_op = stage_transform(stage,m,d,op)
        for ch in range(3):
            yield (['stages',i,stage,x,ch],(p[ch],p[3],mul[ch],offset[ch],actual_op),n[ch])
    yield from rgb(read_samples(EVIDENCE/'r43/native'),'r43')


def measurements(root):
    env = json.loads((root/'normalization-environment.json').read_text())
    if hashlib.sha256((ROOT/'tools/probes/cxform_input_normalization.c').read_bytes()).hexdigest()!=env['source_sha256']:
        raise ValueError('Normalization measurement source changed')
    raw = (root/'normalization.txt').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=env['output_sha256']:
        raise ValueError('Normalization measurements changed')
    rows = [line.split() for line in raw.decode().splitlines()]
    if [int(v[0]) for v in rows]!=list(range(1,256)) or any(len(v)!=7 for v in rows):
        raise ValueError('Incomplete normalization measurements')
    return {mode:{int(v[0]):(from_bits(int(v[1+2*j],16)),from_bits(int(v[2+2*j],16)))
                  for v in rows} for j,mode in enumerate(MODES)}


def sequence(args, table, order):
    c,a,m,d,op = args
    normalized = table[c][0] if c else 0.0
    straight = f32(normalized*table[a][1])
    value = max(0,min(1,f32(f32(straight*f32(m/256))+f32(d/255))))
    opacity = f32((op*256//100)/256)
    if order=='alpha_first':
        value = f32(f32(value*a)*opacity)
    elif order=='opacity_first':
        value = f32(f32(value*opacity)*a)
    elif order=='joint':
        value = f32(value*f32(a*opacity))
    else:
        raise ValueError('Unknown operation order')
    return int(value)


def merged(old, added):
    result = intersect(old,added)
    for value in result.values():
        for field in ('lower_witness','upper_witness'):
            if value[field] and value[field]['key'][0]=='r42':
                value[field]['key'][0] = 'r43'
    return result


def score_sequence(samples, table, order):
    counts = Counter((tuple(args),target) for _,args,target in samples)
    witnesses = {}
    for key,args,target in samples:
        witnesses.setdefault((tuple(args),target),key)
    failures = []
    wrong = 0
    for (args,target),count in counts.items():
        actual = sequence(args,table,order)
        if actual!=target:
            wrong += count
            failures.append({'first_key':witnesses[args,target],'args':list(args),
                             'native':target,'actual':actual,'occurrences':count})
    return {'channels':len(samples),'exact':len(samples)-wrong,
            'failures':failures,'max_delta':max((abs(v['native']-v['actual']) for v in failures),default=0)}


def distinguishing_sequences(sequences):
    result = {}
    for dataset in ('old','new'):
        left = sequences['divide/alpha_first'][dataset]
        right = sequences['multiply_rounded/alpha_first'][dataset]
        index = lambda report: {tuple(v['args'])+(v['native'],):v for v in report['failures']}
        a,b = index(left),index(right)
        differences = []
        for key in sorted(a.keys()|b.keys()):
            witness = a.get(key,b.get(key))
            av = a.get(key,{'actual':witness['native']})['actual']
            bv = b.get(key,{'actual':witness['native']})['actual']
            if av!=bv:
                differences.append({'first_key':witness['first_key'],'args':witness['args'],
                                    'native':witness['native'],'divide':av,'multiply_rounded':bv,
                                    'occurrences':witness['occurrences']})
        result[dataset] = {'differing_channels':sum(v['occurrences'] for v in differences),
                           'witnesses':differences}
    return result


def analyze(root):
    rows,clipping = read_native(root/'native')
    old = prior()
    added = list(rgb(rows,'rejected'))
    green = [v for v in added if v[0][-1]==1]
    measured = coefficient_measurements(EVIDENCE/'r41')
    normal = measurements(root)
    reports = {}
    for space in ('unit','normalized','byte'):
        for order in ORDERS:
            key = space+'/'+order
            bounds = merged(old['models'][key]['green_intervals'],constraints(green,space,order))
            report = {'green_intervals':bounds,'empty_green_alphas':[a for a,v in bounds.items() if v['low_bits']>v['high_bits']]}
            if order=='alpha_first':
                bounds = merged(old['models'][key]['combined_intervals'],constraints(added,space,order))
                report['combined_intervals'] = bounds
                report['empty_combined_alphas'] = [a for a,v in bounds.items() if v['low_bits']>v['high_bits']]
                report['total_constraints'] = old['models'][key]['total_constraints']+len(added)
                candidates = {name:{a:values[name] for a,values in measured.items()} for name in measured[1]}
                # Factorized comparisons are not assumed equivalent to the direct
                # input-normalization sequences evaluated independently below.
                for mode,table in normal.items():
                    candidates['factorized_'+mode] = {a:f32(table[a][1]*table[1][0]) for a in table}
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
                report['membership'] = fits
            reports[key] = report
    previous = list(old_samples())
    if len(previous)!=661248:
        raise ValueError('Old controls omitted')
    sequences = {}
    for mode,table in normal.items():
        for order in ORDERS:
            sequences[mode+'/'+order] = {'old':score_sequence(previous,table,order),
                                       'new':score_sequence(added,table,order)}
    retained = read_samples(EVIDENCE/'r43/native')
    by_input = {(p[3],x,m,d,op):(p,n) for _,x,p,n,m,d,op in rows}
    if any(by_input[p[3],x,m,d,op]!=(p,n) for _,x,p,n,m,d,op in retained):
        raise ValueError('Retained r43 controls changed')
    return {'pixels':len(rows),'alphas':alphas(),'retained_exact':len(retained),
            'clipping':clipping,'models':reports,'direct_sequences':sequences,
            'normalization_discriminators':distinguishing_sequences(sequences),
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze(args.root)
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    print('pixels',report['pixels'],'clipping',len(report['clipping']),'retained',report['retained_exact'])
    for key,v in report['models'].items():
        print(key,'empty',v['empty_green_alphas'],v.get('empty_combined_alphas'),
              {n:m['inside'] for n,m in v.get('membership',{}).items()})
    for key,v in report['direct_sequences'].items():
        print(key,{n:{k:q for k,q in m.items() if k!='failures'} for n,m in v.items()})
    raise SystemExit(1)
