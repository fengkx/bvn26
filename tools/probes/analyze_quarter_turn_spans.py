"""Constrain reversed-axis scan spans with independent clipping and source-byte readbacks."""
import argparse
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.bitmap_half_even_candidate import interpolate


def decode(native,check_ramps=True):
    rows=events(native);assert len(rows)==9617
    source=[];rotated={};cases=[]
    for kind,payload in rows:
        v=payload.split(',')
        if kind=='source':
            assert int(v[0])==len(source)//4 and len(v)==9
            source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='rotated':
            turn,y=map(int,v[:2]);pixels=rotated.setdefault(turn,[])
            assert y==len(pixels)//8 and len(v)==18
            pixels.extend(unpack(list(map(int,v[2:]))))
        elif kind=='case':
            assert int(v[0])==len(cases) and len(v)==18
            cases.append({'key':v,'pixels':[]})
        elif kind=='row':
            pixels=cases[-1]['pixels'];assert int(v[0])==len(pixels)//32 and len(v)==65
            pixels.extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert len(source)==32 and len(cases)==384 and all(len(c['pixels'])==768 for c in cases)
    if check_ramps:assert source==[[16+64*x,16+28*y,73,255] for y in range(8) for x in range(4)]
    for turn in (1,3):
        expected=[None]*32
        for y in range(8):
            for x in range(4):
                xx,yy=(7-y,x) if turn==1 else (y,3-x)
                expected[yy*8+xx]=source[y*4+x]
        assert rotated[turn]==expected
    return source,cases


def coordinates(key,x,y):
    turn=int(key[1]);s=float(key[4]);tx,ty=map(float,key[6:8])
    coefficients=[(0,1/s,-ty/s),(-1/s,0,8+tx/s)] if turn==1 else [(0,-1/s,4+ty/s),(1/s,0,-tx/s)]
    result=[]
    for a,b,t in coefficients:
        ia,ib,it=[math.floor(v*65536+.5) for v in (a,b,t)]
        result.append((x*ia+y*ib+it+round((ia+ib)/2)-32768)/65536)
    return result


def analyze(native):
    source,cases=decode(native);scores={};failures=[];overlap={};excluded=0
    texel=lambda x,y:source[max(0,min(7,y))*4+max(0,min(3,x))]
    for case in cases:
        k=case['key'];turn=int(k[1]);s=float(k[4]);tx,ty=map(float,k[6:8]);left,length=map(int,k[16:])
        assert k[2:4]==['0','false'] and list(map(int,k[8:10]))==[8,4]
        expected=[0,1,-1,0,8,0] if turn==1 else [0,-1,1,0,0,4]
        assert list(map(float,k[10:16]))==expected
        for y in range(24):
            for x in range(32):
                target=case['pixels'][y*32+x]
                if not left<=x<left+length:
                    assert target==[0,0,0,0];continue
                if not (tx<=x and x+1<=tx+8*s and ty<=y and y+1<=ty+4*s):excluded+=1;continue
                key=tuple(k[1:16]+[str(x),str(y)])
                overlap.setdefault(key,[]).append({'clip':[left,length],'native':target})
                u,v=coordinates(k,x,y)
                for order in ('byte','vertical','horizontal'):
                    actual=interpolate(u,v,texel,order);name=f'turn{turn}-length{length}-{order}'
                    score=scores.setdefault(name,{'samples':0,'exact':0,'max_channel_delta':0})
                    score['samples']+=1;score['exact']+=actual==target;score['max_channel_delta']=max(score['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,target)))
                    if actual!=target:failures.append({'key':k,'x':x,'y':y,'uv':[u,v],'order':order,'actual':actual,'native':target})
    changed=[{'key':list(k),'observations':v} for k,v in overlap.items() if len({tuple(o['native']) for o in v})>1]
    return {'scores':scores,'failures':failures,'overlapping_groups':len(overlap),'changed_overlap':changed,'excluded_fringe_or_outside':excluded,'source_pixels_exact':32,'initializer_admitted':False,'interpolation_routing_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for order in ('byte','vertical','horizontal'):
        rows=[v for k,v in r['scores'].items() if k.endswith('-'+order)]
        print(order,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows),max(v['max_channel_delta'] for v in rows))
    print('changed overlap',len(r['changed_overlap']),r['overlapping_groups'])
