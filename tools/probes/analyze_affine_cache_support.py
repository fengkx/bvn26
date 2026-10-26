"""Measure affine cache allocation independently of original component pixels."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_affine_mask_coverage import decode as old_decode
from tools.probes.build_bound_bitmap_component import ROOT

FILTER=[0,0,0,0,57,0,0,0,0,148,0,0,0,0,230,0,0,0,0,255]


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
    for (w,h),pixels in sources.items():assert pixels==[[144,120,8,255]]*(w*h)
    for case in cases:
        k=case['key'];mode=int(k[25]);assert k[26:]==(['false','0'] if mode==0 else ['true',str(int(mode==2))])
        left,top,w,h,ux,uy,uw,uh=map(int,k[17:25])
        assert len(case['pixels'])==w*h
        if not (0<=left<=ux<ux+uw<=left+w<=600 and 0<=top<=uy<uy+uh<=top+h<=400):raise ValueError(f'case{k[0]}: incomplete cache support capture')
    return cases


def bounds(key,method):
    w,h=map(int,key[3:5]);a,b,c,d,tx,ty=map(Fraction,key[5:11]);dx,dy=map(Fraction,key[15:17])
    local=[(Fraction(round(4*(a*x+c*y)),4),Fraction(round(4*(b*x+d*y)),4)) for x,y in ((0,0),(w,0),(w,h),(0,h))]
    translation=[Fraction(round(tx*4)+math.trunc(dx*4),4),Fraction(round(ty*4)+math.trunc(dy*4),4)]
    result=[]
    for axis in range(2):
        lo=min(p[axis] for p in local);hi=max(p[axis] for p in local);t=translation[axis]
        if method=='separate':result.append((math.floor(lo)+math.floor(t),math.ceil(hi)+math.floor(t)+1))
        elif method=='combined':result.append((math.floor(lo+t),math.ceil(hi+t)+1))
        else:
            assert method=='unexpanded';result.append((math.floor(lo+t),math.ceil(hi+t)))
    return [result[0][0],result[1][0],result[0][1]-result[0][0],result[1][1]-result[1][0]]


def analyze(native):
    cases=decode(native);old=old_decode(ROOT/'evidence/importer-loud-fail/r181/native')
    rows=[];scores={};old_exact=0;old_samples=0;pair_exact=0;pair_samples=0
    for i in range(0,len(cases),2):
        first,second=cases[i:i+2];assert first['key'][1]==second['key'][1] and first['key'][3:21]==second['key'][3:21]
        pair_samples+=len(first['pixels']);pair_exact+=sum(a==b for a,b in zip(first['pixels'],second['pixels']))
    for case in cases:
        k=case['key'];ci,kind,mode=int(k[1]),int(k[2]),int(k[25])
        if mode==0:
            prior=old[ci*2+kind];assert k[3:25]==prior['key'][3:25]
            old_samples+=len(case['pixels']);old_exact+=sum(a==b for a,b in zip(case['pixels'],prior['pixels']))
        if mode!=2:continue
        used=list(map(int,k[21:25]));left,top,w,h=map(int,k[17:21])
        alpha_rectangle=all(pixel[3]==(255 if used[0]<=left+i%w<used[0]+used[2] and used[1]<=top+i//w<used[1]+used[3] else 0) for i,pixel in enumerate(case['pixels']))
        colors={}
        for pixel in case['pixels']:
            key=','.join(map(str,pixel));colors[key]=colors.get(key,0)+1
        full_rectangle=all(pixel==([57,148,230,255] if used[0]<=left+i%w<used[0]+used[2] and used[1]<=top+i//w<used[1]+used[3] else [0]*4) for i,pixel in enumerate(case['pixels']))
        predictions={}
        for method in ('separate','combined','unexpanded'):
            predicted=bounds(k,method);predictions[method]=predicted
            s=scores.setdefault(method,{'samples':0,'exact':0,'failures':[]});s['samples']+=1;s['exact']+=predicted==used
            if predicted!=used:s['failures'].append({'case':int(k[0]),'predicted':predicted,'native':used})
        rows.append({'case':int(k[0]),'matrix_properties':k[5:17],'native_support':used,'opaque_alpha_rectangle':alpha_rectangle,'color_counts':colors,'solid_rectangle':full_rectangle,'predictions':predictions})
    return {'source_texels_exact':27621,'cases':198,'unchanged_uncached':{'exact':old_exact,'samples':old_samples},
            'bitmap_vector_pairs':{'exact':pair_exact,'samples':pair_samples},'rows':rows,'scores':scores,
            'cache_allocation_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print(r['unchanged_uncached'],r['bitmap_vector_pairs'],'solid',sum(v['solid_rectangle'] for v in r['rows']))
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'])
