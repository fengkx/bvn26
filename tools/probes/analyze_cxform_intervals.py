"""Constrain one reciprocal per alpha; never render with inferred coefficients."""
import argparse
from functools import lru_cache
import gzip
import json
import math
from pathlib import Path
import struct

from tools.probes.analyze_cxform_alpha import (
    ROOT, alpha_samples, analyze as old_analysis, capture_rows, load_precision,
)
from tools.probes.nested_composition import rgba
from tools.probes.run_nested_filters import unpack

ALPHAS = (6,7,12,14,15,24,28,30,33,35,41,43,45,47,49,51,53,55,59,61,63,67,71,75,
          79,87,91,93,95,103,107,111,119,135,143,151,159,167,175,183,191,199,207,223,231,247)
MULTIPLIERS = (191,192,193,255,257)
OFFSETS = (-1,0,1,7)
OPACITIES = (33,67,100)
CONSTRUCTIONS = ('rounded_inverse','estimate_inverse','estimate_product',
                 'estimate_quotient','rounded_product','scalar_estimate',
                 'estimated_normalizer')
MAX_FINITE = 0x7f7fffff


def f32(value):
    try:
        return struct.unpack('<f',struct.pack('<f',value))[0]
    except OverflowError:
        return math.copysign(math.inf,value)


def float_bits(value):
    return struct.unpack('<I',struct.pack('<f',value))[0]


def from_bits(bits):
    return struct.unpack('<f',struct.pack('<I',bits))[0]


def channel(args, reciprocal, space, order):
    c,alpha,multiplier,offset,opacity = args
    op = f32((opacity*256//100)/256)
    mul = f32(multiplier/256)
    if space=='unit':
        straight = f32(c*reciprocal)
        transformed = f32(f32(straight*mul)+f32(offset/255))
        value,scale = max(0,min(1,transformed)),float(alpha)
    elif space=='normalized':
        straight = f32(f32(c/255)*reciprocal)
        transformed = f32(f32(straight*mul)+f32(offset/255))
        value,scale = max(0,min(1,transformed)),f32(alpha/255)
    elif space=='byte':
        straight = f32(c*reciprocal)
        transformed = f32(f32(straight*mul)+offset)
        value,scale = max(0,min(255,transformed)),f32(alpha/255)
    else:
        raise ValueError('Unknown reciprocal space')
    if order=='alpha_first':
        value = f32(f32(value*scale)*op)
    elif order=='opacity_first':
        value = f32(f32(value*op)*scale)
    elif order=='joint':
        value = f32(value*f32(scale*op))
    else:
        raise ValueError('Unknown multiplication order')
    if space=='normalized':
        value = f32(value*255)
    return int(value)


@lru_cache(maxsize=500000)
def lower_bound(args, space, order, target):
    """First nonnegative finite float coefficient producing at least target.

    Positive multipliers make every tested sequence monotone. MAX_FINITE+1
    means no finite coefficient can reach the target; it is never evaluated.
    """
    lo,hi = 0,MAX_FINITE+1
    while lo<hi:
        mid = (lo+hi)//2
        if channel(args,from_bits(mid),space,order)<target:
            lo = mid+1
        else:
            hi = mid
    return lo


def constraints(samples, space, order):
    intervals = {}
    for key,args,target in samples:
        low = lower_bound(args,space,order,target)
        high = lower_bound(args,space,order,target+1)-1
        a = args[1]
        current = intervals.setdefault(a,{'low_bits':0,'high_bits':MAX_FINITE,
                                         'lower_witness':None,'upper_witness':None})
        witness = {'key':key,'args':list(args),'native_channel':target}
        if low>current['low_bits']:
            current['low_bits'],current['lower_witness'] = low,witness
        if high<current['high_bits']:
            current['high_bits'],current['upper_witness'] = high,witness
    return intervals


def native_samples(directory):
    identities = []
    for a in ALPHAS:
        for m in MULTIPLIERS:
            for d in OFFSETS:
                for op in OPACITIES:
                    identities.append([len(identities),a,m,d,op])
    result = []
    residuals = {(5,12,13,14):0,(62,108,127,135):0}
    for row in capture_rows(directory,identities):
        index,a,m,d,op = row[:5]
        for x in range(32):
            source,native = unpack(row[5+x*4:9+x*4])
            g = (2*min(a,(x+1)*4)*255+a)//(2*a)
            red,blue = (91,237) if a==14 else (117,240)
            if source!=rgba((red<<16)+(g<<8)+blue,a):
                raise ValueError('Explicit native input readback changed')
            if native[3]!=a*(op*256//100)//256:
                raise ValueError('Native opacity alpha changed')
            if tuple(source) in residuals:
                residuals[tuple(source)] += 1
            result.append((index,x,source,native,m,d,op))
    if any(count!=60 for count in residuals.values()):
        raise ValueError('Missing exact residual filter inputs')
    return result


def coefficient_measurements(root):
    rows = [line.split() for line in (root/'reciprocal.txt').read_text().splitlines()]
    if [int(v[0]) for v in rows]!=list(range(1,256)) or any(len(v)!=8 for v in rows):
        raise ValueError('Incomplete common-construction measurements')
    return {int(v[0]):dict(zip(CONSTRUCTIONS,(from_bits(int(b,16)) for b in v[1:]))) for v in rows}


def construction_membership(intervals, measured, space):
    reports = {}
    for name in CONSTRUCTIONS:
        outside = []
        for a,bounds in intervals.items():
            coefficient = measured[a][name]
            if space!='unit':
                coefficient = f32(coefficient*255)
            bits = float_bits(coefficient)
            if not bounds['low_bits']<=bits<=bounds['high_bits']:
                outside.append(a)
        reports[name] = {'inside':len(intervals)-len(outside),'alphas':len(intervals),'outside':outside}
    return reports


def analyze(root):
    native = native_samples(root/'native')
    measured = coefficient_measurements(root)
    previous_measurements = load_precision(ROOT/'evidence/importer-loud-fail/r40/reciprocal.txt')
    if any(measured[a]['estimate_inverse']!=previous_measurements[a][0] for a in measured):
        raise ValueError('Old reciprocal measurement changed')
    green = [(['native',i,x,1],(p[1],p[3],m,d,op),n[1]) for i,x,p,n,m,d,op in native]
    combined = []
    for i,x,p,n,m,d,op in native:
        for ch,mul,offset in ((0,128,8),(1,m,d),(2,256,-4)):
            combined.append((['native',i,x,ch],(p[ch],p[3],mul,offset,op),n[ch]))
    for name,ops in (('alpha',(25,50,100)),('opacity',(1,33,67,99))):
        for key,p,n,op in alpha_samples(ROOT/'evidence/importer-loud-fail/r40'/name,ops):
            if not p[3]:
                continue
            for ch,m,d in ((0,128,8),(1,192,0),(2,256,-4)):
                combined.append(([name,*key,ch],(p[ch],p[3],m,d,op),n[ch]))
    green_reports,combined_reports = {},{}
    for space in ('unit','normalized','byte'):
        for order in ('alpha_first','opacity_first','joint'):
            key = space+'/'+order
            intervals = constraints(green,space,order)
            failures = []
            for location,args,target in green:
                a = args[1]
                rec = previous_measurements[a][0 if space=='unit' else 2]
                actual = channel(args,rec,space,order)
                if actual!=target:
                    failures.append({'key':location,'args':list(args),'actual':actual,'native':target})
            green_reports[key] = {
                'samples':len(green),'exact':len(green)-len(failures),'failures':failures,
                'intervals':{str(a):v for a,v in intervals.items()},'measurements':construction_membership(intervals,measured,space)}
            if order=='alpha_first':
                bounds = constraints(combined,space,order)
                combined_reports[space] = {'constraints':len(combined),'intervals':{str(a):v for a,v in bounds.items()},
                                          'measurements':construction_membership(bounds,measured,space)}
    # An inferred interval is only a rejection/identification constraint, never
    # a source of coefficients for a renderer or a per-alpha lookup table.
    old = old_analysis(ROOT/'evidence/importer-loud-fail/r40')
    regression = {}
    for group in ('prior_regressions','all_alpha','native_boundaries','normalized_prior'):
        regression[group] = {k:{a:b for a,b in v.items() if a!='failures'} for k,v in old[group].items()}
    return {'production_admitted':False,'candidate_admitted':False,'gpu_advance_allowed':False,
            'native_rows':len(native)//32,'native_pixels':len(native),'green':green_reports,
            'combined':combined_reports,'old_regressions':regression,
            'scope':'Coefficient feasibility intervals only. No inferred coefficient is rendered or admitted; no ISA inference.'}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze(args.root)
    payload = (json.dumps(report,indent=2)+'\n').encode()
    args.output.write_bytes(gzip.compress(payload,mtime=0) if args.output.suffix=='.gz' else payload)
    for group in ('green','combined'):
        print(group,{k:{'empty':sum(b['low_bits']>b['high_bits'] for b in v['intervals'].values()),
                        'samples':v.get('samples',v.get('constraints')),'exact':v.get('exact'),
                        'construction_fit':{n:r['inside'] for n,r in v['measurements'].items()}}
                     for k,v in report[group].items()})
    raise SystemExit(1)
