"""Reject whole source-normalization sequences; never use inferred reciprocals."""
import argparse
from functools import lru_cache
import gzip
import json
from pathlib import Path

from tools.probes.analyze_cxform_intervals import MAX_FINITE, f32, from_bits, float_bits, coefficient_measurements
from tools.probes.analyze_cxform_rejected import measurements
from tools.probes.analyze_cxform_signed_bounds import controls, EVIDENCE
from tools.probes.cxform_signed_bounds import validate


@lru_cache(maxsize=1)
def normalizers():
    return measurements(EVIDENCE/'r44')


def channel(args, reciprocal, mode):
    c,a,m,d,op = args
    source = normalizers()[mode][c][0] if c else 0.0
    value = f32(f32(f32(source*reciprocal)*f32(m/256))+f32(d/255))
    return int(f32(f32(max(0,min(1,value))*a)*f32((op*256//100)/256)))


@lru_cache(maxsize=500000)
def interval(args, mode, target):
    validate(args)
    if target<0 or int(target)!=target:
        raise ValueError('Native target must be a nonnegative integer')
    c,_,m,_,_ = args
    if c==0 or m==0:
        return (0,MAX_FINITE) if channel(args,0,mode)==target else (MAX_FINITE+1,MAX_FINITE)

    def first(bound):
        lo,hi = 0,MAX_FINITE+1
        while lo<hi:
            mid = (lo+hi)//2
            actual = channel(args,from_bits(mid),mode)
            before = actual<bound if m>0 else actual>bound
            if before:
                lo = mid+1
            else:
                hi = mid
        return lo

    return (first(target),first(target+(1 if m>0 else -1))-1)


def analyze():
    old,signed = controls()
    samples = old+signed
    measured = coefficient_measurements(EVIDENCE/'r41')
    models = {}
    for mode in normalizers():
        bounds = {}
        for key,args,target in samples:
            lo,hi = interval(tuple(args),mode,target)
            value = bounds.setdefault(args[1],{'low_bits':0,'high_bits':MAX_FINITE,
                                               'lower_witness':None,'upper_witness':None})
            witness = {'key':key,'args':args,'native':target}
            if lo>value['low_bits']:
                value['low_bits'],value['lower_witness'] = lo,witness
            if hi<value['high_bits']:
                value['high_bits'],value['upper_witness'] = hi,witness
        membership = {}
        for name in measured[1]:
            outside = [a for a,v in bounds.items() if not v['low_bits']<=float_bits(f32(measured[a][name]*255))<=v['high_bits']]
            membership[name] = {'inside':len(bounds)-len(outside),'outside':outside}
        models[mode] = {'intervals':bounds,'empty_alphas':[a for a,v in bounds.items() if v['low_bits']>v['high_bits']],
                        'membership':membership}
        print(mode,'empty',models[mode]['empty_alphas'],flush=True)
    return {'models':models,'old_constraints':len(old),'signed_constraints':len(signed),
            'old_bounds_retained_not_reinterpreted':True,'coefficients_selected':False,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = analyze()
    args.output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    raise SystemExit(1)
