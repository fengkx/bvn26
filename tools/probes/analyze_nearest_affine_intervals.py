"""Use native source-index intervals only to reject independently defined affine constructions."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_nearest_affine import decode,inverse


def analyze(native):
    _,cases=decode(native);rows=[];scores={};constraints=0
    for case in cases:
        coeff=inverse(case['key']);points=[]
        for y in range(40):
            for x in range(40):
                corners=[[a*xx+b*yy+t for a,b,t in coeff] for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1))]
                if not all(1<=v<=15 for p in corners for v in p):continue
                pixel=case['pixels'][y*40+x];assert pixel[2:]==[73,255] and all((c-8)%15==0 for c in pixel[:2])
                points.append((x,y,[(c-8)//15 for c in pixel[:2]]))
        constraints+=len(points)*2
        for family in ('exact','fixed16'):
            for dimension,(a,b,t) in enumerate(coeff):
                if family=='fixed16':a,b,t=[Fraction(math.floor(v*65536+Fraction(1,2)),65536) for v in (a,b,t)]
                lows=[(Fraction(index[dimension])-a*x-b*y,(x,y,index[dimension])) for x,y,index in points]
                lo,wlo=max(lows);hi,whi=min((v+1,w) for v,w in lows)
                candidates={'corner':t,'center':t+(a+b)/2,'horizontal_center':t+a/2,'vertical_center':t+b/2}
                if family=='fixed16':candidates['rounded_half_step']=t+Fraction(round((a+b)*32768),65536)
                accepted={k:lo<=v<hi for k,v in candidates.items()}
                for k,value in accepted.items():
                    score=scores.setdefault(family+'/'+k,{'intervals':0,'inside':0});score['intervals']+=1;score['inside']+=value
                rows.append({'key':case['key'],'dimension':dimension,'family':family,'constraints':len(points),'lower_inclusive':str(lo),'upper_exclusive':str(hi),'lower_witness':list(wlo),'upper_witness':list(whi),'feasible':lo<hi,'candidate_intercepts':{k:str(v) for k,v in candidates.items()},'candidate_inside':accepted})
    return {'source_index_constraints':constraints,'coefficient_feasibility':{family:{'intervals':sum(r['family']==family for r in rows),'feasible':sum(r['family']==family and r['feasible'] for r in rows)} for family in ('exact','fixed16')},'construction_scores':scores,'intervals':rows,'coefficients_selected_from_intervals':False,'affine_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print(r['coefficient_feasibility']);print(r['construction_scores'])
