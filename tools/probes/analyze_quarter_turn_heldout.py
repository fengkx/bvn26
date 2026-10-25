"""Hold the signed initializer and geometric partition fixed on distant, larger-source controls."""
import argparse
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.bitmap_half_even_candidate import interpolate


def decode(native):
    rows=events(native);assert len(rows)==27025
    source=[];rotated={};cases=[]
    for kind,payload in rows:
        v=payload.split(',')
        if kind=='source':
            assert int(v[0])==len(source)//4 and len(v)==9
            source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='rotated':
            turn,y=map(int,v[:2]);pixels=rotated.setdefault(turn,[])
            assert y==len(pixels)//16 and len(v)==34
            pixels.extend(unpack(list(map(int,v[2:]))))
        elif kind=='case':
            assert int(v[0])==len(cases) and len(v)==18
            cases.append({'key':v,'pixels':[]})
        elif kind=='row':
            pixels=cases[-1]['pixels'];assert int(v[0])==len(pixels)//32 and len(v)==65
            pixels.extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert len(source)==64 and len(cases)==1080 and all(len(c['pixels'])==768 for c in cases)
    for turn in (1,3):
        expected=[None]*64
        for y in range(16):
            for x in range(4):
                xx,yy=(15-y,x) if turn==1 else (y,3-x)
                expected[yy*16+xx]=source[y*4+x]
        assert rotated[turn]==expected
    return source,cases


def coordinates(key,x,y):
    turn=int(key[1]);s=float(key[4]);tx,ty=map(float,key[6:8])
    coefficients=[(0,1/s,-ty/s),(-1/s,0,16+tx/s)] if turn==1 else [(0,-1/s,4+ty/s),(1/s,0,-tx/s)]
    result=[]
    for a,b,t in coefficients:
        ia,ib,it=[math.floor(v*65536+.5) for v in (a,b,t)]
        result.append((x*ia+y*ib+it+round((ia+ib)/2)-32768)/65536)
    return result


def partition(key,y):
    s=float(key[4]);tx,ty=map(float,key[6:8]);clip,length=map(int,key[16:])
    left=max(clip,math.ceil(tx));right=min(clip+length,math.floor(tx+16*s),32)
    xs=list(range(left,right));uv=[coordinates(key,x,y) for x in xs];bulk=set()
    for chunk in range(0,len(xs),256):
        end=min(chunk+256,len(xs));start,stop=chunk,end
        while start<stop and not (1<=uv[start][0]<3 and 1<=uv[start][1]<15):start+=1
        while stop>start and not (1<=uv[stop-1][0]<3 and 1<=uv[stop-1][1]<15):stop-=1
        assert all(1<=u<3 and 1<=v<15 for u,v in uv[start:stop])
        bulk.update(xs[start:start+(stop-start)//4*4])
    return xs,uv,bulk


def analyze(native):
    source,cases=decode(native);scores={o:{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]} for o in ('vertical','horizontal')}
    texel=lambda x,y:source[max(0,min(15,y))*4+max(0,min(3,x))]
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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
