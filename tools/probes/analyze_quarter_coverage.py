"""Independently test quarter-grid rectangle coverage from explicit premultiplied input bytes."""
import argparse
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


def analyze(native):
    records=events(native);assert len(records)==23121
    inputs={};cases=[]
    for kind,payload in records:
        v=payload.split(',')
        if kind=='input':
            phase,ci,alpha,color=map(int,v[:4]);assert alpha==[0,1,2,31,63,64,127,128,254,255][phase]
            assert color==[0,1,17,63,127,128,254,255][ci]
            raw=unpack(list(map(int,v[4:])));assert len(raw)==1 and raw[0][3]==alpha
            inputs[phase,ci]=raw[0]
        elif kind=='case':
            assert len(v)==16 and int(v[0])==len(cases);cases.append({'key':v,'pixels':[]})
        elif kind=='row':
            pixels=cases[-1]['pixels'];assert int(v[0])==len(pixels)//8 and len(v)==17
            pixels.extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert len(inputs)==80 and len(cases)==2560 and all(len(c['pixels'])==64 for c in cases)
    scores={};failures=[]
    for case in cases:
        k=case['key'];phase,ci,turn=map(int,k[1:4]);assert list(map(float,k[4:6]))==[1,1]
        tx,ty=map(float,k[6:8]);w,h=map(int,k[8:10]);assert (w,h)==((4,3) if turn==0 else (3,4))
        assert list(map(float,k[10:]))==([1,0,0,1,0,0] if turn==0 else [0,1,-1,0,3,0])
        raw=inputs[phase,ci]
        for y in range(8):
            for x in range(8):
                area=max(0,min(x+1,tx+w)-max(x,tx))*max(0,min(y+1,ty+h)-max(y,ty))
                assert area*16==int(area*16)
                actual=[math.floor(v*area) for v in raw];target=case['pixels'][y*8+x]
                domain='outside' if area==0 else ('interior' if area==1 else 'fringe')
                score=scores.setdefault(domain,{'samples':0,'exact':0,'max_channel_delta':0})
                score['samples']+=1;score['exact']+=actual==target;score['max_channel_delta']=max(score['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,target)))
                if actual!=target:failures.append({'key':k,'x':x,'y':y,'source':raw,'coverage':area,'actual':actual,'native':target})
    return {'inputs':[{'phase':p,'color_index':c,'rgba':v} for (p,c),v in inputs.items()],'scores':scores,'failures':failures,'quarter_grid_constant_coverage_exact':not failures,'general_coverage_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print(json.dumps(r['scores'],indent=2))
