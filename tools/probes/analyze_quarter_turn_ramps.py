"""Test one signed fixed-point affine initializer independently of interpolation routing."""
import argparse
import json
import math
from pathlib import Path
from tools.probes.analyze_quarter_turn_equivalence import decode
from tools.probes.bitmap_half_even_candidate import interpolate


def coordinates(key,x,y):
    turn=int(key[1]);scale=float(key[4]);tx,ty=map(float,key[6:8])
    # Invert the complete authored matrix before independently quantizing its coefficients.
    if int(key[2])==1:coefficients=[(1/scale,0,-tx/scale),(0,1/scale,-ty/scale)]
    else:coefficients=[[(1/scale,0,-tx/scale),(0,1/scale,-ty/scale)],
                      [(0,1/scale,-ty/scale),(-1/scale,0,3+tx/scale)],
                      [(-1/scale,0,4+tx/scale),(0,-1/scale,3+ty/scale)],
                      [(0,-1/scale,4+ty/scale),(1/scale,0,-tx/scale)]][turn]
    result=[]
    for a,b,t in coefficients:
        ia,ib,it=[math.floor(v*65536+.5) for v in (a,b,t)]
        result.append((x*ia+y*ib+it+round((ia+ib)/2)-32768)/65536)
    return result


def analyze(native):
    source,rotated,cases=decode(native);scores={};failures=[];excluded=0
    for case in cases:
        k=case['key'];turn,mode=int(k[1]),int(k[2]);scale=float(k[4]);tx,ty=map(float,k[6:8]);rw,rh=map(int,k[8:10])
        raw=source if mode==0 else rotated[turn];sw,sh=(4,3) if mode==0 else (rw,rh)
        texel=lambda x,y:raw[max(0,min(sh-1,y))*sw+max(0,min(sw-1,x))]
        for y in range(24):
            for x in range(32):
                if not (tx<=x and x+1<=tx+rw*scale and ty<=y and y+1<=ty+rh*scale):
                    excluded+=1;continue
                target=case['pixels'][y*32+x];u,v=coordinates(k,x,y)
                for order in ('byte','vertical','horizontal'):
                    actual=interpolate(u,v,texel,order)
                    name=f'turn{turn}-mode{mode}-cache{k[3]}-{order}'
                    score=scores.setdefault(name,{'samples':0,'exact':0,'max_channel_delta':0})
                    score['samples']+=1;score['exact']+=actual==target;score['max_channel_delta']=max(score['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,target)))
                    if actual!=target:failures.append({'key':k,'x':x,'y':y,'uv':[u,v],'order':order,'actual':actual,'native':target})
    return {'scores':scores,'failures':failures,'excluded_fringe_or_outside':excluded,'initializer_admitted':False,'interpolation_routing_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for order in ('byte','vertical','horizontal'):
        rows=[v for k,v in r['scores'].items() if k.endswith('-'+order)]
        print(order,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows),max(v['max_channel_delta'] for v in rows))
