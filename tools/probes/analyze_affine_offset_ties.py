"""Measure signed offset ties with independent scale, source and target controls."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_rounded_footprint import indices,prepare
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


def analyze(native):
    source=[];samples=[]
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='source':
            assert int(v[0])==len(source)//16 and len(v)==33
            source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='sample':
            assert len(v)==23 and int(v[0])==len(samples)
            samples.append((v[:21],unpack(list(map(int,v[21:])))[0]))
        else:assert [kind,payload]==['done','ok']
    assert source==[[x,y,73,255] for y in range(16) for x in range(16)] and len(samples)==1440
    scores={};tie_samples=0
    for k,pixel in samples:
        phase,pi,ti,di=map(int,k[1:5]);axis=phase//8;scale=(3,5,7,13,-3,-5,-7,-13)[phase%8]
        cm=list(map(Fraction,k[5:11]));assert cm==([scale,0,0,1,0,0] if axis==0 else [1,0,0,scale,0,0])
        position=(4,8,12)[pi];target=(0,1,7,16,31,63)[ti];delta=(Fraction(-1,2),Fraction(-1,4),0,Fraction(1,4),Fraction(1,2))[di]
        assert list(map(int,k[17:21]))==[position,position,target,target]
        draw=[1,0,0,1,Fraction(target)+Fraction(1,2)-cm[0]*position+(delta if axis==0 else 0),Fraction(target)+Fraction(1,2)-cm[3]*position+(delta if axis==1 else 0)]
        assert list(map(Fraction,k[11:17]))==draw
        co=inverse_signed(k[:17]);assert pixel[2:]==[73,255]
        assert all(1<=a*x+b*y+t<=15 for a,b,t in co for x,y in ((target,target),(target+1,target),(target,target+1),(target+1,target+1)))
        tie_samples+=any(v[4] for v in prepare(tuple(co),'half_up'))
        for family in ('half_up','ties_even','ties_away'):
            actual=indices(co,target,target,family)+[73,255]
            s=scores.setdefault(f'{scale}/{axis}/{family}',{'samples':0,'exact':0,'max_source_index_delta':0,'failures':[]})
            s['samples']+=1;s['exact']+=actual==pixel
            s['max_source_index_delta']=max(s['max_source_index_delta'],max(abs(a-b) for a,b in zip(actual,pixel)))
            if actual!=pixel:s['failures'].append({'key':k,'actual':actual,'native':pixel})
    return {'source_texels_exact':256,'samples':1440,'offset_tie_samples':tie_samples,'scores':scores,
            'candidate_admitted':False,'gpu_advance_allowed':True,'gpu_scope':'diagnostic opaque interior only','production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for family in ('half_up','ties_even','ties_away'):
        rows=[v for k,v in r['scores'].items() if k.endswith('/'+family)]
        print(family,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows))
    print('ties',r['offset_tie_samples'])
