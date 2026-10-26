"""Separate declared fill translation from independently tested consumption rules."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_nearest_affine import inverse


def analyze(native):
    records=events(native);assert len(records)==3887;source=[];samples=[]
    for kind,payload in records:
        v=payload.split(',')
        if kind=='source':assert int(v[0])==len(source)//16 and len(v)==33;source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='sample':assert len(v)==25 and int(v[0])==len(samples);samples.append({'key':v[:23],'pixel':unpack(list(map(int,v[23:])))[0]})
        else:assert [kind,payload]==['done','ok']
    assert source==[[x,y,73,255] for y in range(16) for x in range(16)] and len(samples)==3870
    groups={};scores={}
    for sample in samples:
        k=sample['key'];phase,axis,step,position=map(int,k[1:5]);delta=Fraction(step,64);assert list(map(Fraction,k[17:19]))==([delta,0] if axis==0 else [0,delta]);x,y=map(int,k[21:23]);pixel=sample['pixel'];assert pixel[2:]==[73,255] and all(0<=v<16 for v in pixel[:2])
        co=inverse(k[:17]);assert all(1<=a*xx+b*yy+t<=15 for a,b,t in co for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1)))
        fixed=[[math.floor(v*65536+Fraction(1,2)) for v in row] for row in co];q=[Fraction(a*x+b*y+t+round(Fraction(a+b,2)),65536) for a,b,t in fixed]
        rules={'declared':delta,'twip_trunc':Fraction(math.trunc(delta*20),20),'twip_floor':Fraction(math.floor(delta*20),20),'twip_even':Fraction(round(delta*20),20),'twip_away':Fraction((1 if delta>=0 else -1)*math.floor(abs(delta)*20+Fraction(1,2)),20)}
        groups.setdefault((phase,axis,position),[]).append({'step':step,'declared':str(delta),'pixel':pixel})
        for name,d in rules.items():
            actual=[math.floor(v-(d if i==axis else 0)) for i,v in enumerate(q)]+[73,255]
            r=scores.setdefault(f'phase{phase}/{name}',{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]});r['samples']+=1;r['exact']+=actual==pixel;r['max_channel_delta']=max(r['max_channel_delta'],max(abs(v-w) for v,w in zip(actual,pixel)))
            if actual!=pixel:r['failures'].append({'key':k,'actual':actual,'native':pixel})
    rows=[]
    for key,values in groups.items():
        assert [v['step'] for v in values]==list(range(-64,65));phase,axis,position=key
        lo=max(Fraction(v['pixel'][axis])+Fraction(v['declared']) for v in values);hi=min(Fraction(v['pixel'][axis])+Fraction(v['declared'])+1 for v in values)
        clo=max(Fraction(v['pixel'][axis])+Fraction(math.trunc(Fraction(v['declared'])*20),20) for v in values);chi=min(Fraction(v['pixel'][axis])+Fraction(math.trunc(Fraction(v['declared'])*20),20)+1 for v in values)
        rows.append({'consumed_linear_lower':str(clo),'consumed_linear_upper':str(chi),'consumed_linear_feasible':clo<chi,'phase':phase,'axis':axis,'position':position,'declared_linear_lower':str(lo),'declared_linear_upper':str(hi),'declared_linear_feasible':lo<hi,'other_channel_values':sorted({v['pixel'][1-axis] for v in values}),'nonmonotone_steps':[b['step'] for a,b in zip(values,values[1:]) if b['pixel'][axis]>a['pixel'][axis]],'transitions':[b for a,b in zip(values,values[1:]) if a['pixel']!=b['pixel']]})
    return {'source_texels_exact':256,'samples':3870,'scores':scores,'groups':rows,'fill_matrix_is_declared_not_internal_readback':True,'affine_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
    print('declared linear feasible',sum(v['declared_linear_feasible'] for v in r['groups']),len(r['groups']));print('consumed linear feasible',sum(v['consumed_linear_feasible'] for v in r['groups']),len(r['groups']))
