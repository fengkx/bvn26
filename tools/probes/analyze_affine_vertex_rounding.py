"""Isolate authored edge consumption and device-quarter vertex rounding."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack

FAMILIES=('quarter_half_up','quarter_even','quarter_half_down','twip_trunc_then_half_up','twip_even_then_half_up','twip_half_up_then_half_up')


def quantize(value,family):
    if family=='quarter_even':return Fraction(round(value*4),4)
    if family=='quarter_half_down':return Fraction(math.ceil(value*4-Fraction(1,2)),4)
    if family=='twip_trunc_then_half_up':value=Fraction(math.trunc(value*20),20)
    elif family=='twip_even_then_half_up':value=Fraction(round(value*20),20)
    elif family=='twip_half_up_then_half_up':value=Fraction(math.floor(value*20+Fraction(1,2)),20)
    else:assert family=='quarter_half_up'
    return Fraction(math.floor(value*4+Fraction(1,2)),4)


def decode(native):
    source=[];cases=[]
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='source':
            assert int(v[0])==len(source)//64 and len(v)==129
            source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='case':
            assert len(v)==34 and int(v[0])==len(cases)
            cases.append({'key':v,'pixels':[]})
        elif kind=='row':
            p=cases[-1]['pixels'];k=cases[-1]['key'];left,top,w,h=map(int,k[26:30])
            assert int(v[0])==top+len(p)//w and len(v)==1+w*2
            p.extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert source==[[144,120,8,255]]*4096 and len(cases)==840
    for case in cases:
        k=case['key'];left,top,w,h,ux,uy,uw,uh=map(int,k[26:])
        if not(len(case['pixels'])==w*h and 0<=left<=ux<ux+uw<=left+w<=128 and 0<=top<=uy<uy+uh<=top+h<=128):
            raise ValueError(f'case{k[0]}: incomplete vertex coverage capture')
    return cases


def analyze(native):
    cases=decode(native);scores={};bounds_exact=0;pairs=[];bounds=[]
    for i in range(0,len(cases),2):
        a,b=cases[i:i+2];assert a['key'][1]==b['key'][1] and a['key'][3:30]==b['key'][3:30]
        pairs.append({'case':int(a['key'][1]),'samples':len(a['pixels']),'exact':sum(p==q for p,q in zip(a['pixels'],b['pixels']))})
    for case in cases:
        k=case['key'];scale=Fraction(k[3]);edge,step=map(int,k[4:6]);authored=list(map(Fraction,k[6:10]));local=list(map(Fraction,k[10:14]))
        expected=list(map(Fraction,(8,25,8,21)));expected[edge]+=Fraction(step,20);assert authored==expected
        bounds_exact+=local==authored;bounds.append({'case':int(k[0]),'authored':list(map(str,authored)),'local':list(map(str,local))})
        assert list(map(Fraction,k[14:20]))==[scale,0,0,scale,0,0] and list(map(Fraction,k[20:26]))==[1,0,0,1,40,40]
        xs=[local[0]*scale+40,local[1]*scale+40];ys=[local[2]*scale+40,local[3]*scale+40]
        left,top,w,h=map(int,k[26:30])
        for family in FAMILIES:
            x0,x1=sorted(int(quantize(v,family)*4) for v in xs);y0,y1=sorted(int(quantize(v,family)*4) for v in ys)
            s=scores.setdefault(family,{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]})
            for i,pixel in enumerate(case['pixels']):
                x=left+i%w;y=top+i//w
                count=max(0,min(4*x+4,x1)-max(4*x,x0))*max(0,min(4*y+4,y1)-max(4*y,y0))
                actual=[v*count//16 for v in (144,120,8,255)]
                s['samples']+=1;s['exact']+=actual==pixel;s['max_channel_delta']=max(s['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,pixel)))
                if actual!=pixel:s['failures'].append({'case':int(k[0]),'edge':edge,'step':step,'scale':str(scale),'x':x,'y':y,'actual':actual,'native':pixel})
    return {'source_texels_exact':4096,'cases':840,'local_bounds_exact':bounds_exact,'bounds_readbacks':bounds,'storage_pairs':pairs,'scores':scores,
            'negative_device_coordinates_proved':False,'coverage_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print('bounds',r['local_bounds_exact'],r['cases']);print('storage',sum(v['exact'] for v in r['storage_pairs']),sum(v['samples'] for v in r['storage_pairs']))
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
