"""Test globally fixed cache-origin constructions using coordinate-coded native inputs."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_affine_cache_support import FILTER, bounds
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_rounded_footprint import prepare
from tools.probes.analyze_cache_affine_candidate import f32


def decode(native):
    sources={};cases=[]
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='source':
            w,h,y=map(int,v[:3]);s=sources.setdefault((w,h),[])
            assert y==len(s)//w and len(v)==3+2*w
            s.extend(unpack(list(map(int,v[3:]))))
        elif kind=='case':
            assert len(v)==28 and int(v[0])==len(cases)
            cases.append({'key':v,'pixels':[]})
        elif kind=='filter':
            assert cases[-1]['key'][25]=='2' and 'filter' not in cases[-1]
            cases[-1]['filter']=list(map(Fraction,v));assert cases[-1]['filter']==FILTER
        elif kind=='row':
            case=cases[-1];left,top,width,height=map(int,case['key'][17:21])
            assert int(v[0])==top+len(case['pixels'])//width and len(v)==1+2*width
            case['pixels'].extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert set(sources)=={(17,13),(137,200)} and len(cases)==198
    for (w,h),pixels in sources.items():assert pixels==[[x,y,73,255] for y in range(h) for x in range(w)]
    for case in cases:
        k=case['key'];mode=int(k[25]);assert k[26:]==(['false','0'] if mode==0 else ['true',str(int(mode==2))])
        left,top,w,h,ux,uy,uw,uh=map(int,k[17:25]);assert len(case['pixels'])==w*h
        if not (0<=left<=ux<ux+uw<=left+w<=600 and 0<=top<=uy<uy+uh<=top+h<=400):raise ValueError(f'case{k[0]}: incomplete cache coordinate capture')
    return cases


def local_translation(key, origin, method):
    a,b,c,d,tx,ty=map(Fraction,key[5:11]);dx,dy=map(Fraction,key[15:17])
    t=[round(tx*4)+math.trunc(dx*4),round(ty*4)+math.trunc(dy*4)]
    if method=='baseline':return [(Fraction(v,4)-o) for v,o in zip(t,origin)]
    factor=f32(4*f32(.05))
    a,b,c,d=[f32(factor*f32(float(v))) for v in (a,b,c,d)]
    det=f32(f32(a*d)-f32(b*c));reciprocal=f32(1/det)
    inverse=[f32(d*reciprocal),f32(-c*reciprocal),f32(-b*reciprocal),f32(a*reciprocal)]
    def dot(x,y,u,v):
        if method=='rounded_products':return round(f32(x*u))+round(f32(y*v))
        assert method=='rounded_sum';return round(f32(f32(x*u)+f32(y*v)))
    lx=-dot(inverse[0],inverse[1],origin[0]*4,origin[1]*4)
    ly=-dot(inverse[2],inverse[3],origin[0]*4,origin[1]*4)
    return [Fraction(dot(a,c,lx,ly)+t[0],4),Fraction(dot(b,d,lx,ly)+t[1],4)]


def sample(fixed,x,y):
    return [(a*x+b*y+t+offset)//65536 for a,b,t,offset,_ in fixed]


def analyze(native):
    cases=decode(native);scores={};details=[];replicates={'exact':0,'samples':0}
    for i in range(0,len(cases),2):
        a,b=cases[i:i+2];assert a['key'][1]==b['key'][1] and a['key'][3:]==b['key'][3:]
        replicates['samples']+=len(a['pixels']);replicates['exact']+=sum(p==q for p,q in zip(a['pixels'],b['pixels']))
    for case in cases:
        k=case['key'];mode=int(k[25]);w,h=map(int,k[3:5])
        if mode==2:continue
        left,top,width,height=map(int,k[17:21]);co=inverse_signed(k)
        direct=prepare(tuple(co),'ties_even');origin=bounds(k,'separate')[:2]
        methods={'uncached':(direct,[0,0])} if mode==0 else {}
        translations={}
        if mode==1:
            for method in ('baseline','rounded_sum','rounded_products'):
                t=local_translation(k,origin,method);translations[method]=list(map(str,t))
                key=k[:];key[9:11]=list(map(str,t));key[15:17]=['0','0']
                methods[method]=(prepare(tuple(inverse_signed(key)),'ties_even'),origin)
        selected=0
        for i,pixel in enumerate(case['pixels']):
            x,y=left+i%width,top+i//width
            # Fully covered interiors are chosen solely from original source geometry.
            if not all(1<=a*x+b*y+t+min(0,a)+min(0,b) and a*x+b*y+t+max(0,a)+max(0,b)<=limit-1 for (a,b,t),limit in zip(co,(w,h))):continue
            selected+=1
            for method,(fixed,offset) in methods.items():
                ix,iy=sample(fixed,x-offset[0],y-offset[1]);assert 0<=ix<w and 0<=iy<h
                actual=[ix,iy,73,255];s=scores.setdefault(method,{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]})
                s['samples']+=1;s['exact']+=actual==pixel;s['max_channel_delta']=max(s['max_channel_delta'],max(abs(p-q) for p,q in zip(actual,pixel)))
                if actual!=pixel:s['failures'].append({'case':int(k[0]),'x':x,'y':y,'actual':actual,'native':pixel})
        details.append({'case':int(k[0]),'mode':mode,'selected_interior':selected,'origin':origin,'local_translations':translations})
    return {'source_texels_exact':27621,'replicates':replicates,'scores':scores,'cases':details,
            'cache_initializer_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
