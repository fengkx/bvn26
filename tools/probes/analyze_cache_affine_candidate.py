"""Reject static affine-operation hypotheses against independent native cache rows."""
import argparse
import json
import math
from pathlib import Path
import struct
from tools.probes.analyze_bitmap_cache_matrix_bits import decode as binary_cases
from tools.probes.analyze_bitmap_cache_left_bounds import analyze as bounds_cases
from tools.probes.analyze_bitmap_cache_width import ROOT, sample


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def fixed_multiply(a, b):
    return (a*b + 32768) >> 16


def local_translation(scale, translation, origin, method):
    # The static inverse and composition branches round each translation product
    # before addition. Their use by the cache renderer remains unverified.
    twips = round(translation*20)
    offset = origin*20
    if method == 'fixed_inverse_compose':
        forward = round(scale*65536)
        reciprocal = math.floor(4294967296/forward + 0.5)
        local = fixed_multiply(offset, reciprocal) - fixed_multiply(twips, reciprocal)
        return -fixed_multiply(local, forward)/20
    if method == 'float_inverse_compose':
        forward = f32(scale)
        reciprocal = f32(1/forward)
        local = round(f32(f32(offset)*reciprocal)) - round(f32(f32(twips)*reciprocal))
        return -round(f32(f32(local)*forward))/20
    raise ValueError(method)


def controls():
    result=[]
    cases,_=binary_cases(ROOT/'evidence/importer-loud-fail/r104/native')
    for c in cases:
        i,_,_,_,_,_,outer,scale,inner,bmin,_,_=c['key']
        result.append(('r104',int(i),scale,inner,outer,bmin,c['cached']))
    for c in bounds_cases(ROOT/'evidence/importer-loud-fail/r109/native')['cases']:
        i,_,_,scale,inner,outer,_,_,bmin,_=c['key']
        rgb=[[(v>>shift)&255 for shift in (16,8,0)] for v in c['cached']]
        result.append(('r109',int(i),scale,inner,outer,bmin,rgb))
    return result


def analyze():
    result={}
    for suite,i,scale,inner,outer,bmin,actual in controls():
        origin=math.floor(bmin+outer)
        effective=round(inner*4)/4+math.trunc(outer*4)/4
        positions=[x for x in range(len(actual)) if effective+scale<=x and x+1<=effective+15*scale]
        for method in ('baseline','fixed_inverse_compose','float_inverse_compose'):
            translation=effective-origin if method=='baseline' else local_translation(scale,inner+outer,origin,method)
            key=suite+'/'+method
            score=result.setdefault(key,{'samples':0,'exact':0,'max_channel_delta':0,'counterexamples':[]})
            for x in positions:
                predicted=sample(scale,translation,x-origin,16)
                score['samples']+=1
                if predicted==actual[x]:score['exact']+=1
                else:
                    score['max_channel_delta']=max(score['max_channel_delta'],max(abs(a-b) for a,b in zip(predicted,actual[x])))
                    if len(score['counterexamples'])<12:
                        score['counterexamples'].append({'case':i,'x':x,'scale':scale,'inner':inner,'outer':outer,'origin':origin,'local_translation':translation,'predicted':predicted,'native':actual[x]})
    return {'comparisons':result,'static_routing_verified':False,'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze();a.output.write_text(json.dumps(r,indent=2)+'\n')
    for k,v in r['comparisons'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
