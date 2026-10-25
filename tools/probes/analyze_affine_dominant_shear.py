"""Discriminate negative-component constructions using dominant reflected shears."""
import argparse
from fractions import Fraction
import json
from pathlib import Path

from tools.probes.analyze_affine_negative_terms import FAMILIES, indices
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_scale_split import property_float32
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack

MATRICES = [(-1,0,-2,1),(-1,0,2,1),(1,-2,0,-1),(1,2,0,-1),
            (-2,0,-2,1),(-2,0,2,1),(1,-2,0,-2),(1,2,0,-2)]


def analyze(native):
    source, cases, samples = [], [], []
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='source':
            assert int(v[0])==len(source)//16 and len(v)==33
            source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='case':
            assert len(v)==15 and int(v[0])==len(cases)
            cases.append({'key':v,'pixels':[]})
        elif kind=='row':
            pixels=cases[-1]['pixels'];assert int(v[0])==64+len(pixels)//128 and len(v)==257
            pixels.extend(unpack(list(map(int,v[1:]))))
        elif kind=='sample':
            assert len(v)==19 and int(v[0])==len(samples)
            samples.append((v[:17],unpack(list(map(int,v[17:])))[0]))
        else:assert [kind,payload]==['done','ok']
    assert source==[[x,y,73,255] for y in range(16) for x in range(16)]
    assert len(cases)==16 and len(samples)==6192
    full={};pairs=[]
    for case in cases:
        k=case['key'];phase,factor=int(k[1]),int(k[4]);assert k[2:4]==['0','0'] and factor in (1,64)
        cm=list(map(property_float32,k[5:11]));assert cm[4:]==[0,0]
        assert [v*factor for v in cm[:4]]==list(MATRICES[phase])
        x,y,w,h=map(int,k[11:]);assert 64<=x<x+w<=192 and 64<=y<y+h<=192
        pixels=case['pixels'];assert len(pixels)==16384;full[phase,factor]=pixels
        if factor==64:
            base=full[phase,1]
            pairs.append({'phase':phase,'samples':16384,'exact':sum(a==b for a,b in zip(pixels,base)),
                          'max_channel_delta':max(abs(a-b) for p,q in zip(pixels,base) for a,b in zip(p,q))})
    groups={};scores={};zero=0
    for k,pixel in samples:
        phase,axis,step,position=int(k[1]),int(k[4]),int(k[5]),int(k[6]);assert k[2:4]==['0','0']
        cm=list(map(property_float32,k[7:13]));assert cm[4:]==[0,0] and [v*64 for v in cm[:4]]==list(MATRICES[phase])
        key=['0']*5+[str(v*64) for v in cm[:4]]+['0','0','1','0','0','1','128','128']
        co=inverse_signed(key);x,y=map(int,k[15:17]);assert pixel[2:]==[73,255]
        delta=[Fraction(0),Fraction(0)];delta[axis]=Fraction(step,64)
        assert all(1<=a*xx+b*yy+t-d<=15 for (a,b,t),d in zip(co,delta) for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1)))
        if step==0:zero+=full[phase,1][(y-64)*128+x-64]==pixel
        corner=co[axis][0]*x+co[axis][1]*y+co[axis][2]
        groups.setdefault((phase,axis,position,corner),[]).append({'step':step,'pixel':pixel})
        for family in FAMILIES:
            actual=indices(co,x,y,family,delta)+[73,255]
            s=scores.setdefault(f'{phase}/{family}',{'samples':0,'exact':0,'max_source_index_delta':0,'failures':[]})
            s['samples']+=1;s['exact']+=actual==pixel
            s['max_source_index_delta']=max(s['max_source_index_delta'],max(abs(a-b) for a,b in zip(actual,pixel)))
            if actual!=pixel:s['failures'].append({'key':k,'actual':actual,'native':pixel})
    rows=[]
    for (phase,axis,position,corner),values in groups.items():
        assert [v['step'] for v in values]==list(range(-64,65))
        lo=max(Fraction(v['pixel'][axis])+Fraction(v['step'],64) for v in values)
        hi=min(Fraction(v['pixel'][axis])+Fraction(v['step'],64)+1 for v in values)
        rows.append({'phase':phase,'matrix':list(MATRICES[phase]),'axis':axis,'position':position,
                     'lower':str(lo),'upper':str(hi),'feasible':lo<hi,'corner':str(corner),
                     'offset_lower':str(lo-corner),'offset_upper':str(hi-corner),
                     'other_channel_values':sorted({v['pixel'][1-axis] for v in values}),
                     'nonmonotone_steps':[b['step'] for a,b in zip(values,values[1:]) if b['pixel'][axis]>a['pixel'][axis]]})
    return {'source_texels_exact':256,'samples':6192,'zero_phase_pairs':pairs,
            'zero_phase_scalar':{'samples':48,'exact':zero},'groups':rows,'scores':scores,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print('zero full',sum(v['exact'] for v in r['zero_phase_pairs']));print('zero scalar',r['zero_phase_scalar'])
    for family in FAMILIES:
        rows=[v for k,v in r['scores'].items() if k.endswith('/'+family)]
        print(family,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows))
