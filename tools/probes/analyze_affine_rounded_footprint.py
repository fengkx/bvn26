"""Retain all native observations while testing one rounded minimum footprint."""
import argparse
from fractions import Fraction
from functools import lru_cache
import json
import math
from pathlib import Path

from tools.probes.affine_control_samples import samples as prior_samples
from tools.probes.analyze_affine_footprint import floor_surd
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_scale_split import property_float32
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


def samples(root):
    yield from prior_samples(root)
    for number in (174,175):
        for kind,payload in events(root/f'r{number}/native'):
            if kind!='sample':continue
            v=payload.split(',');pixel=unpack(list(map(int,v[-2:])))[0];assert pixel[2:]==[73,255]
            if number==174:
                key=['0']*5+[str(property_float32(c)*64) for c in v[7:11]]+['0','0','1','0','0','1','128','128']
                x,y=map(int,v[15:17]);delta=[Fraction(0),Fraction(0)];delta[int(v[4])]=Fraction(int(v[5]),64)
            else:
                key=['0']*5+v[4:16];x,y=map(int,v[16:18]);delta=(0,0)
            yield f'r{number}',v[:-2],inverse_signed(key),x,y,pixel[:2],delta


@lru_cache(maxsize=None)
def prepare(coefficients,family):
    assert family in ('half_up','ties_even','ties_away')
    rows=[]
    for row in coefficients:
        a,b,t=[math.floor(v*65536+Fraction(1,2)) for v in row]
        minimum=min(0,a,b);square=Fraction(a*a+b*b,4)
        lower=floor_surd(Fraction(minimum),square)
        offset=floor_surd(Fraction(minimum)+Fraction(1,2),square)
        at_tie=(Fraction(lower)+Fraction(1,2)-minimum)**2==square
        if at_tie and family=='ties_even':offset=lower if lower%2==0 else lower+1
        if at_tie and family=='ties_away':offset=lower if lower<0 else lower+1
        rows.append((a,b,t,offset,at_tie))
    return rows


def indices(coefficients,x,y,family,delta=(0,0)):
    return [math.floor(Fraction(a*x+b*y+t+offset,65536)-d)
            for (a,b,t,offset,_),d in zip(prepare(tuple(coefficients),family),delta)]


def analyze(root):
    scores={};tie_samples=0
    for suite,key,co,x,y,native,delta in samples(root):
        tie_samples+=any(v[4] for v in prepare(tuple(co),'half_up'))
        for family in ('half_up','ties_even','ties_away'):
            actual=indices(co,x,y,family,delta)
            s=scores.setdefault(suite+'/'+family,{'samples':0,'exact':0,'max_source_index_delta':0,'failures':[]})
            s['samples']+=1;s['exact']+=actual==native
            s['max_source_index_delta']=max(s['max_source_index_delta'],max(abs(a-b) for a,b in zip(actual,native)))
            if actual!=native:s['failures'].append({'key':key,'actual':actual,'native':native})
    return {'scores':scores,'offset_tie_samples':tie_samples,'candidate_admitted':False,
            'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,default=Path('evidence/importer-loud-fail'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.evidence);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for family in ('half_up','ties_even','ties_away'):
        rows=[v for k,v in r['scores'].items() if k.endswith('/'+family)]
        print(family,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows))
    print('tie samples',r['offset_tie_samples'])
