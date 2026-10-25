"""Compare common negative-component constructions, never RGB-selected routes."""
import argparse
from fractions import Fraction
from functools import lru_cache
import json
import math
from pathlib import Path

from tools.probes.affine_control_samples import samples
from tools.probes.analyze_affine_footprint import floor_surd

FAMILIES=('negative_sum','negative_minimum','negative_diagonal_priority')


@lru_cache(maxsize=None)
def prepare(coefficients,family):
    assert family in FAMILIES
    rows=[]
    for axis,row in enumerate(coefficients):
        a,b,t=[Fraction(math.floor(v*65536+Fraction(1,2)),65536) for v in row]
        diagonal,other=(a,b) if axis==0 else (b,a)
        negative={'negative_sum':min(0,a)+min(0,b),'negative_minimum':min(0,a,b),
                  'negative_diagonal_priority':diagonal if diagonal<0 else min(0,other)}[family]
        rows.append((a,b,t+negative,(a*a+b*b)/4))
    return rows


def indices(coefficients,x,y,family,delta=(0,0)):
    return [floor_surd(a*x+b*y+t-d,square) for (a,b,t,square),d in zip(prepare(tuple(coefficients),family),delta)]


def analyze(root):
    scores={}
    for suite,key,co,x,y,native,delta in samples(root):
        for family in FAMILIES:
            actual=indices(co,x,y,family,delta)
            s=scores.setdefault(suite+'/'+family,{'samples':0,'exact':0,'max_source_index_delta':0,'failures':[]})
            s['samples']+=1;s['exact']+=actual==native
            s['max_source_index_delta']=max(s['max_source_index_delta'],max(abs(a-b) for a,b in zip(actual,native)))
            if actual!=native:s['failures'].append({'key':key,'x':x,'y':y,'actual':actual,'native':native})
    return {'scores':scores,'coefficients_selected_from_intervals':False,'candidate_admitted':False,
            'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,default=Path('evidence/importer-loud-fail'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.evidence);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for family in FAMILIES:
        rows=[v for k,v in r['scores'].items() if k.endswith('/'+family)]
        print(family,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows))
