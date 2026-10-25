"""Reject common affine subpixel coverage constructions against constant-source controls."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


def decode(native):
    sources={};cases=[]
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='source':
            w,h,y=map(int,v[:3]);raw=sources.setdefault((w,h),[])
            assert y==len(raw)//w and len(v)==3+2*w
            raw.extend(unpack(list(map(int,v[3:]))))
        elif kind=='case':
            assert len(v)==25 and int(v[0])==len(cases)
            cases.append({'key':v,'pixels':[]})
        elif kind=='row':
            k=cases[-1]['key'];pixels=cases[-1]['pixels'];left,top,w,h=map(int,k[17:21])
            assert int(v[0])==top+len(pixels)//w and len(v)==1+2*w
            pixels.extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert set(sources)=={(17,13),(137,200)}
    for (w,h),raw in sources.items():assert raw==[[144,120,8,255]]*(w*h)
    assert len(cases)==66
    for case in cases:
        k=case['key'];left,top,w,h,ux,uy,uw,uh=map(int,k[17:])
        if len(case['pixels'])!=w*h:raise ValueError(f"{native}/game/main.swf:case_{k[0]}: incomplete capture rows")
        if not (0<=left<=ux<ux+uw<=left+w<=600 and 0<=top<=uy<uy+uh<=top+h<=400):
            raise ValueError(f"{native}/game/main.swf:case_{k[0]}: capture ROI excludes native nonzero bounds {k[21:]}")
    return cases


def inverse_exact(key):
    a,b,c,d,tx,ty=map(Fraction,key[5:11]);dx,dy=map(Fraction,key[15:17]);tx+=dx;ty+=dy;det=a*d-b*c
    assert det!=0
    return [(d/det,-c/det,(c*ty-d*tx)/det),(-b/det,a/det,(b*tx-a*ty)/det)]


def integer_rows(coefficients,width,height):
    rows=[]
    for (a,b,t),limit in zip(coefficients,(width,height)):
        den=math.lcm(a.denominator,b.denominator,t.denominator)
        rows.append((int(a*den),int(b*den),int(t*den)*8,8*den*limit))
    return rows


def coverage(rows,x,y,grid):
    result=0
    for dy in grid:
        for dx in grid:
            result+=all(0<=a*(8*x+dx)+b*(8*y+dy)+t<limit for a,b,t,limit in rows)
    return result


def analyze(native):
    cases=decode(native);pairs=[];scores={};alpha_values=set()
    for i in range(0,len(cases),2):
        bitmap,vector=cases[i:i+2];assert bitmap['key'][1]==vector['key'][1] and bitmap['key'][3:21]==vector['key'][3:21]
        pairs.append({'case':int(bitmap['key'][1]),'bitmap_used_bounds':bitmap['key'][21:],'vector_used_bounds':vector['key'][21:],'samples':len(bitmap['pixels']),
                      'exact':sum(a==b for a,b in zip(bitmap['pixels'],vector['pixels'])),
                      'max_channel_delta':max(abs(v-w) for a,b in zip(bitmap['pixels'],vector['pixels']) for v,w in zip(a,b))})
    for case in cases:
        k=case['key'];width,height=map(int,k[3:5]);left,top,w,h=map(int,k[17:21])
        co=inverse_signed(k[:17]);exact=inverse_exact(k[:17])
        models={'center_consumed':(integer_rows(co,width,height),(1,3,5,7)),
                'lower_consumed':(integer_rows(co,width,height),(0,2,4,6)),
                'upper_consumed':(integer_rows(co,width,height),(2,4,6,8)),
                'center_unquantized_translation':(integer_rows(exact,width,height),(1,3,5,7))}
        for name,(rows,grid) in models.items():
            r=scores.setdefault(name,{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]})
            for i,pixel in enumerate(case['pixels']):
                x=left+i%w;y=top+i//w;count=coverage(rows,x,y,grid);actual=[v*count//16 for v in (144,120,8,255)]
                r['samples']+=1;r['exact']+=actual==pixel;r['max_channel_delta']=max(r['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,pixel)))
                if actual!=pixel:r['failures'].append({'case':int(k[1]),'kind':int(k[2]),'x':x,'y':y,'coverage_count':count,'actual':actual,'native':pixel})
        alpha_values.update(v[3] for v in case['pixels'])
    return {'source_texels_exact':27621,'cases':66,'case_metadata':[v['key'] for v in cases],'storage_pairs':pairs,'native_alpha_values':sorted(alpha_values),
            'scores':scores,'coverage_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print('storage',sum(v['exact'] for v in r['storage_pairs']),sum(v['samples'] for v in r['storage_pairs']))
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
    print('alphas',r['native_alpha_values'])
