"""Test one geometric four-pixel partition with globally fixed bulk interpolation orders."""
import argparse
import json
import math
from pathlib import Path
from tools.probes.analyze_quarter_turn_spans import decode,coordinates
from tools.probes.bitmap_half_even_candidate import interpolate


def partition(key,y):
    s=float(key[4]);tx,ty=map(float,key[6:8]);clip,length=map(int,key[16:])
    left=max(clip,math.ceil(tx));right=min(clip+length,math.floor(tx+8*s),32)
    xs=list(range(left,right));uv=[coordinates(key,x,y) for x in xs];bulk=set()
    for chunk in range(0,len(xs),256):
        end=min(chunk+256,len(xs));start,stop=chunk,end
        while start<stop and not (1<=uv[start][0]<3 and 1<=uv[start][1]<7):start+=1
        while stop>start and not (1<=uv[stop-1][0]<3 and 1<=uv[stop-1][1]<7):stop-=1
        assert all(1<=u<3 and 1<=v<7 for u,v in uv[start:stop])
        bulk.update(xs[start:start+(stop-start)//4*4])
    return xs,uv,bulk


def analyze(native,ramps):
    source,cases=decode(native,check_ramps=ramps);scores={o:{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]} for o in ('vertical','horizontal')}
    texel=lambda x,y:source[max(0,min(7,y))*4+max(0,min(3,x))]
    for case in cases:
        k=case['key'];s=float(k[4]);ty=float(k[7])
        for y in range(math.ceil(ty),min(24,math.floor(ty+4*s))):
            xs,uv,bulk=partition(k,y)
            for x,(u,v) in zip(xs,uv):
                target=case['pixels'][y*32+x]
                for order,score in scores.items():
                    actual=interpolate(u,v,texel,order if x in bulk else 'byte');score['samples']+=1;score['exact']+=actual==target
                    score['max_channel_delta']=max(score['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,target)))
                    if actual!=target:score['failures'].append({'key':k,'x':x,'y':y,'uv':[u,v],'bulk':x in bulk,'actual':actual,'native':target})
    return {'source':source,'scores':scores,'partition_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--ramps',action='store_true');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native,a.ramps);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
