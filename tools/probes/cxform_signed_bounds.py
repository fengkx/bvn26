"""Exact reciprocal feasibility bounds for consumed positive/zero/negative CXFORM."""
from functools import lru_cache
import math

from tools.probes.analyze_cxform_intervals import (
    MAX_FINITE, channel, from_bits, lower_bound,
)


def validate(args):
    c,a,m,d,op = args
    if not all(math.isfinite(v) for v in args):
        raise ValueError('Nonfinite CXFORM control')
    if c<0 or a<=0 or op<0:
        raise ValueError('Signed bounds require nonnegative color/opacity and positive alpha')
    if int(m)!=m or int(d)!=d:
        raise ValueError('Signed bounds require consumed 1/256 multipliers and integer offsets')


@lru_cache(maxsize=200000)
def first_at_most(args, space, order, target):
    """First finite nonnegative coefficient whose decreasing output is <= target."""
    validate(args)
    if args[0]<=0 or args[2]>=0:
        raise ValueError('Decreasing search requires positive source and negative multiplier')
    lo,hi = 0,MAX_FINITE+1
    while lo<hi:
        mid = (lo+hi)//2
        if channel(args,from_bits(mid),space,order)>target:
            lo = mid+1
        else:
            hi = mid
    return lo


@lru_cache(maxsize=200000)
def interval(args, space, order, target):
    validate(args)
    if target<0 or int(target)!=target:
        raise ValueError('Native channel must be a nonnegative integer')
    c,_,m,_,_ = args
    if c==0 or m==0:
        # Avoid evaluating an overflowing intermediate followed by 0*infinity.
        # These channels are independent of the reciprocal coefficient.
        return (0,MAX_FINITE) if channel(args,0.0,space,order)==target else (MAX_FINITE+1,MAX_FINITE)
    if m<0:
        return (first_at_most(args,space,order,target),
                first_at_most(args,space,order,target-1)-1)
    return (lower_bound(args,space,order,target),
            lower_bound(args,space,order,target+1)-1)


def constraints(samples, space, order):
    result = {}
    for key,args,target in samples:
        low,high = interval(tuple(args),space,order,target)
        value = result.setdefault(args[1],{'low_bits':0,'high_bits':MAX_FINITE,
                                          'lower_witness':None,'upper_witness':None})
        witness = {'key':key,'args':list(args),'native_channel':target}
        if low>value['low_bits']:
            value['low_bits'],value['lower_witness'] = low,witness
        if high<value['high_bits']:
            value['high_bits'],value['upper_witness'] = high,witness
    return result
