"""Separate reflected coordinate phase from zero-phase scale-path changes."""
import argparse
from fractions import Fraction
import json
from pathlib import Path

from tools.probes.analyze_affine_footprint import indices
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_scale_split import property_float32
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack

MATRICES = [(1,0,0,1),(-1,0,0,1),(1,0,0,-1),(-1,0,0,-1),
            (-1,0,.5,1),(-1,0,-.5,1),(1,.5,0,-1),(1,-.5,0,-1),
            (-1,.5,0,1),(-1,-.5,0,1),(1,0,.5,-1),(1,0,-.5,-1)]


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
            pixels=cases[-1]['pixels'];assert int(v[0])==96+len(pixels)//64 and len(v)==129
            pixels.extend(unpack(list(map(int,v[1:]))))
        elif kind=='sample':
            assert len(v)==19 and int(v[0])==len(samples)
            samples.append((v[:17],unpack(list(map(int,v[17:])))[0]))
        else:assert [kind,payload]==['done','ok']
    assert source==[[x,y,73,255] for y in range(16) for x in range(16)]
    assert len(cases)==24 and len(samples)==9288
    full={};pairs=[]
    for case in cases:
        k=case['key'];phase,factor=int(k[1]),int(k[4]);assert k[2:4]==['0','0'] and factor in (1,64)
        cm=list(map(property_float32,k[5:11]));assert cm[4:]==[0,0]
        assert [v*factor for v in cm[:4]]==list(MATRICES[phase])
        x,y,w,h=map(int,k[11:]);assert 96<=x<x+w<=160 and 96<=y<y+h<=160
        pixels=case['pixels'];assert len(pixels)==4096;full[phase,factor]=pixels
        if factor==64:
            base=full[phase,1]
            pairs.append({'phase':phase,'samples':4096,'exact':sum(a==b for a,b in zip(pixels,base)),
                          'max_channel_delta':max(abs(a-b) for p,q in zip(pixels,base) for a,b in zip(p,q))})
    groups={};scores={};zero=0
    for k,pixel in samples:
        phase,axis,step,position=int(k[1]),int(k[4]),int(k[5]),int(k[6]);assert k[2:4]==['0','0']
        cm=list(map(property_float32,k[7:13]));assert cm[4:]==[0,0] and [v*64 for v in cm[:4]]==list(MATRICES[phase])
        key=['0']*5+[str(v*64) for v in cm[:4]]+['0','0','1','0','0','1','128','128']
        co=inverse_signed(key);x,y=map(int,k[15:17]);assert pixel[2:]==[73,255]
        delta=[Fraction(0),Fraction(0)];delta[axis]=Fraction(step,64)
        assert all(1<=a*xx+b*yy+t-d<=15 for (a,b,t),d in zip(co,delta) for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1)))
        if step==0:zero+=full[phase,1][(y-96)*64+x-96]==pixel
        corner=co[axis][0]*x+co[axis][1]*y+co[axis][2]
        groups.setdefault((phase,axis,position,corner),[]).append({'step':step,'pixel':pixel})
        actual=indices(co,x,y,'fixed_inverse',delta)+[73,255]
        s=scores.setdefault(str(phase),{'samples':0,'exact':0,'max_source_index_delta':0,'failures':[]})
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
    return {'source_texels_exact':256,'samples':9288,'zero_phase_pairs':pairs,
            'zero_phase_scalar':{'samples':72,'exact':zero},'groups':rows,'scores':scores,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print('zero full',sum(v['exact'] for v in r['zero_phase_pairs']));print('zero scalar',r['zero_phase_scalar'])
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_source_index_delta'])
