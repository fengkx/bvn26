"""Native channel-identity and explicit materialization controls; fail closed."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

from tools.probes.analyze_cxform_alpha import ROOT, capture_rows
from tools.probes.analyze_cxform_intervals import (
    ALPHAS, OPACITIES, channel, coefficient_measurements, constraints,
    construction_membership, f32,
)
from tools.probes.nested_composition import rgba
from tools.probes.run_nested_filters import unpack

MULTIPLIERS = (255,256,257)
STAGE_ALPHAS = (7,14,93,135,146,197,206,210,229,231,244)
STAGE_NAMES = ('combined','multiplier_only','offset_only','multiplier_then_offset','offset_then_multiplier')


def expected_source(alpha, x):
    green = (2*min(alpha,(x+1)*4)*255+alpha)//(2*alpha)
    red,blue = (91,237) if alpha==14 else (117,240)
    return rgba((red<<16)+(green<<8)+blue,alpha)


def read_identity(directory):
    identities = []
    for a in ALPHAS:
        for m in MULTIPLIERS:
            for op in OPACITIES:
                identities.append([len(identities),a,m,0,op])
    return read_generated(directory,identities)


def read_zero(directory):
    identities = []
    for a in (6,14,135,146,197,231,244,255):
        for d in (1,7,64,127,255):
            for op in OPACITIES:
                identities.append([len(identities),a,256,d,op])
    return read_generated(directory,identities,zero_green=True)


def read_generated(directory, identities, zero_green=False):
    result = []
    for row in capture_rows(directory,identities):
        index,a,m,d,op = row[:5]
        for x in range(32):
            source,native = unpack(row[5+x*4:9+x*4])
            expected = expected_source(a,x)
            if zero_green:
                expected[1] = 0
            if source!=expected:
                raise ValueError('Identity source readback changed')
            if native[3]!=a*(op*256//100)//256:
                raise ValueError('Identity alpha changed')
            result.append((index,x,source,native,m,d,op))
    return result


def read_stages(directory):
    identities = []
    case = 0
    for a in STAGE_ALPHAS:
        for m in MULTIPLIERS:
            for d in (-1,0,1):
                for op in OPACITIES:
                    identities.extend([case,a,m,d,op,stage] for stage in range(5))
                    case += 1
    result = []
    outputs = {}
    for row in capture_rows(directory,identities):
        index,a,m,d,op,stage = row[:6]
        for x in range(32):
            source,native = unpack(row[6+x*4:10+x*4])
            expected = expected_source(a,x) if stage<3 else outputs[index,stage-2,x]
            if source!=expected:
                raise ValueError('Materialized input does not equal the recorded prior buffer')
            actual_op = 100 if stage in (1,2) else op
            if native[3]!=source[3]*(actual_op*256//100)//256:
                raise ValueError('Materialized alpha changed')
            outputs[index,stage,x] = native
            result.append((index,stage,x,source,native,m,d,op))
    return result


def stage_transform(stage, m, d, op):
    if stage==0:
        return (128,m,256),(8,d,-4),op
    if stage in (1,4):
        return (128,m,256),(0,0,0),100 if stage==1 else op
    if stage in (2,3):
        return (256,256,256),(8,d,-4),100 if stage==2 else op
    raise ValueError('Unknown materialized stage')


def merge_intervals(previous, added):
    merged = copy.deepcopy(previous)
    for interval in merged.values():
        for field in ('lower_witness','upper_witness'):
            if interval[field]:
                interval[field]['key'] = ['r41',*interval[field]['key']]
    for a,interval in added.items():
        a = str(a)
        if a not in merged:
            merged[a] = copy.deepcopy(interval)
            continue
        current = merged[a]
        if interval['low_bits']>current['low_bits']:
            current['low_bits'],current['lower_witness'] = interval['low_bits'],interval['lower_witness']
        if interval['high_bits']<current['high_bits']:
            current['high_bits'],current['upper_witness'] = interval['high_bits'],interval['upper_witness']
    return merged


def read_previous():
    root = ROOT/'evidence/importer-loud-fail/r41'
    provenance = json.loads((root/'provenance.json').read_text())
    for name in ('intervals.json.gz','reciprocal.txt'):
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=provenance['output_sha256'][name]:
            raise ValueError('Pinned r41 evidence changed')
    return json.loads(gzip.decompress((root/'intervals.json.gz').read_bytes()))


def membership(intervals, measured, space):
    return construction_membership({int(a):v for a,v in intervals.items()},measured,space)


def analyze(root):
    identity = read_identity(root/'native')
    stages = read_stages(root/'stages')
    zero = read_zero(root/'zero')
    previous = read_previous()
    measured = coefficient_measurements(ROOT/'evidence/importer-loud-fail/r41')
    bypass = {}
    for op in OPACITIES:
        rows = [v for v in identity if v[4]==256 and v[6]==op]
        failures = []
        for i,x,source,native,m,d,_ in rows:
            expected = source[1]*(op*256//100)//256
            if expected!=native[1]:
                failures.append({'key':['identity',i,x,1],'source':source,'native':native,
                                 'identity_bypass_green':expected})
        bypass[str(op)] = {'samples':len(rows),'exact':len(rows)-len(failures),'failures':failures}
    green = [(['identity',i,x,1],(p[1],p[3],m,d,op),n[1]) for i,x,p,n,m,d,op in identity]
    combined = []
    for i,x,p,n,m,d,op in identity:
        for ch,mul,offset in ((0,128,8),(1,m,d),(2,256,-4)):
            combined.append((['identity',i,x,ch],(p[ch],p[3],mul,offset,op),n[ch]))
    for i,x,p,n,m,d,op in zero:
        for ch,mul,offset in ((0,128,8),(1,m,d),(2,256,-4)):
            combined.append((['zero',i,x,ch],(p[ch],p[3],mul,offset,op),n[ch]))
    for i,stage,x,p,n,m,d,op in stages:
        mul,offset,actual_op = stage_transform(stage,m,d,op)
        for ch in range(3):
            combined.append((['stages',i,stage,x,ch],(p[ch],p[3],mul[ch],offset[ch],actual_op),n[ch]))
    reports = {}
    combined_reports = {}
    for space in ('unit','normalized','byte'):
        for order in ('alpha_first','opacity_first','joint'):
            key = space+'/'+order
            added = constraints(green,space,order)
            merged = merge_intervals(previous['green'][key]['intervals'],added)
            reports[key] = {'intervals':merged,'empty_alphas':[int(a) for a,v in merged.items() if v['low_bits']>v['high_bits']],
                            'measurements':membership(merged,measured,space)}
            if order=='alpha_first':
                added = constraints(combined,space,order)
                merged = merge_intervals(previous['combined'][space]['intervals'],added)
                failures = []
                for location,args,target in combined:
                    coefficient = measured[args[1]]['estimate_inverse' if space=='unit' else 'estimate_quotient']
                    if space!='unit':
                        coefficient = f32(coefficient*255)
                    actual = channel(args,coefficient,space,order)
                    if actual!=target:
                        failures.append({'key':location,'args':list(args),'actual':actual,'native':target})
                combined_reports[space] = {
                    'new_constraints':len(combined),
                    'total_constraints':previous['combined'][space]['constraints']+len(combined),
                    'intervals':merged,'empty_alphas':[int(a) for a,v in merged.items() if v['low_bits']>v['high_bits']],
                    'measured_new_exact':len(combined)-len(failures),'failures':failures,
                    'measurements':membership(merged,measured,space)}
    outputs = {(i,stage,x):n for i,stage,x,p,n,m,d,op in stages}
    materialized = {}
    for stage in (3,4):
        failures = []
        green_differences = 0
        maximum = [0]*4
        count = 0
        for i,s,x,p,n,m,d,op in stages:
            if s!=stage:
                continue
            direct = outputs[i,0,x]
            count += 1
            green_differences += n[1]!=direct[1]
            maximum = [max(old,abs(a-b)) for old,a,b in zip(maximum,direct,n)]
            if n!=direct:
                failures.append({'key':[i,stage,x],'one_draw':direct,'materialized':n})
        materialized[STAGE_NAMES[stage]] = {
            'samples':count,'same_rgba_as_one_draw':count-len(failures),
            'different_green_channels':green_differences,'max_channel_difference':maximum,
            'failures':failures,
            'meaning':'Native-vs-native observations; these operations are not assumed equivalent.'}
    zero_report = {}
    for denominator in (255,256):
        failures = []
        for i,x,p,n,m,d,op in zero:
            actual = int(f32(f32(f32(d/denominator)*p[3])*f32((op*256//100)/256)))
            if actual!=n[1]:
                failures.append({'key':['zero',i,x,1],'actual':actual,'native':n[1]})
        zero_report[str(denominator)] = {'samples':len(zero),'exact':len(zero)-len(failures),'failures':failures}
    return {'production_admitted':False,'candidate_admitted':False,'gpu_advance_allowed':False,
            'identity_pixels':len(identity),'materialized_pixels':len(stages),
            'identity_bypass':bypass,'zero_offset':zero_report,'green_intersections':reports,'combined_intersections':combined_reports,
            'materialization':materialized,
            'scope':'No interval endpoint is rendered; no channel bypass, inferred coefficient table or routing change admitted.'}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze(args.root)
    payload = (json.dumps(report,indent=2)+'\n').encode()
    args.output.write_bytes(gzip.compress(payload,mtime=0) if args.output.suffix=='.gz' else payload)
    for group in ('identity_bypass','zero_offset','combined_intersections','materialization'):
        print(group,{k:{a:b for a,b in v.items() if a not in ('failures','intervals','measurements')}
                     for k,v in report[group].items()})
    raise SystemExit(1)
