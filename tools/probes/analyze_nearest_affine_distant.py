"""Constrain affine step coefficients with independent distant coordinate-coded source points."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_nearest_affine import inverse


def analyze(native):
    records=events(native);assert len(records)==769;source=[];samples=[]
    for kind,payload in records:
        v=payload.split(',')
        if kind=='source':assert int(v[0])==len(source)//128 and len(v)==257;source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='sample':assert len(v)==23 and int(v[0])==len(samples);samples.append({'key':v[:21],'pixel':unpack(list(map(int,v[21:])))[0]})
        else:assert [kind,payload]==['done','ok']
    assert source==[[x,y,73,255] for y in range(128) for x in range(128)] and len(samples)==640
    groups={};scores={}
    for sample in samples:
        k=sample['key'];pixel=sample['pixel'];assert pixel[2:]==[73,255] and all(0<=v<128 for v in pixel[:2]);sx,sy,x,y=map(int,k[17:]);a,b,c,d,tx,ty=map(Fraction,k[5:11]);dx,dy=map(Fraction,k[15:17])
        assert x==math.floor(a*sx+c*sy+tx+dx) and y==math.floor(b*sx+d*sy+ty+dy)
        co=inverse(k[:17]);assert all(1<=aa*xx+bb*yy+t<=127 for aa,bb,t in co for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1)))
        groups.setdefault(tuple(k[1:17]),[]).append(sample)
        fixed=[[math.floor(v*65536+Fraction(1,2)) for v in row] for row in co]
        routes={'exact_inverse_center':[math.floor(aa*(x+Fraction(1,2))+bb*(y+Fraction(1,2))+t) for aa,bb,t in co],'fixed_inverse_center':[(aa*x+bb*y+t+round(Fraction(aa+bb,2)))//65536 for aa,bb,t in fixed]}
        for name,indices in routes.items():
            actual=[*indices,73,255];r=scores.setdefault(name,{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]});r['samples']+=1;r['exact']+=actual==pixel;r['max_channel_delta']=max(r['max_channel_delta'],max(abs(v-w) for v,w in zip(actual,pixel)))
            if actual!=pixel:r['failures'].append({'key':k,'actual':actual,'native':pixel})
    intervals=[]
    for key,values in groups.items():
        assert len(values)==16;co=inverse(values[0]['key'][:17])
        for family in ('exact','fixed16'):
            for axis,(a,b,t) in enumerate(co):
                if family=='fixed16':a,b,t=[Fraction(math.floor(v*65536+Fraction(1,2)),65536) for v in (a,b,t)]
                bounds=[(Fraction(v['pixel'][axis])-a*int(v['key'][19])-b*int(v['key'][20]),v['key'][19:21]+[str(v['pixel'][axis])]) for v in values]
                lo,wlo=max(bounds);hi,whi=min((v+1,w) for v,w in bounds)
                intervals.append({'key':list(key),'axis':axis,'family':family,'lower_inclusive':str(lo),'upper_exclusive':str(hi),'lower_witness':wlo,'upper_witness':whi,'feasible':lo<hi})
    return {'source_texels_exact':16384,'samples':640,'scores':scores,'intervals':intervals,'coefficient_feasibility':{f:{'intervals':sum(v['family']==f for v in intervals),'feasible':sum(v['family']==f and v['feasible'] for v in intervals)} for f in ('exact','fixed16')},'coefficients_selected_from_intervals':False,'affine_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print(r['coefficient_feasibility'])
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
