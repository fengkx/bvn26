"""Discriminate fixed-coordinate interpolation modes under independently varied clips."""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
from tools.probes.analyze_blur_kernel_heldout import ROOT
from tools.probes.bitmap_sampling_candidate import coordinates
from tools.probes.bitmap_repeat_span_candidate import sample
from tools.probes.run_nested_filters import unpack

SX,SY=1.23333740234375,1.24481201171875
YS=(20,21,26,27,28)


def texel(pattern,x,y):
    x,y=max(0,min(59,x)),max(0,min(57,y))
    red=255*int(y%2*2+x%2==pattern) if pattern<4 else (x if pattern==4 else y)%2*255
    return [red,113,113]


def decode(native):
    build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    events=[s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    assert len(events)==949 and events[-1][6:]==['done','ok']
    for i,row in enumerate(events):assert row[1]==build['run_id'] and row[2:6]==[str(i),'0','0','0']
    pos=0;result=[];input_exact=0
    for tx,pattern in itertools.product((4,4.25),range(6)):
        for y in range(58):
            row=events[pos];pos+=1;values=list(map(float,row[7].split(',')))
            assert row[6]=='source' and values[:3]==[tx,pattern,y] and len(values)==63
            for x,packed in enumerate(values[3:]):
                p=int(packed)&0xffffffff
                assert [(p>>s)&255 for s in (16,8,0)]==texel(pattern,x,y) and p>>24==255
                input_exact+=1
        for kind,left,right in [(0,l,r) for l in range(4,8) for r in range(76,81)]+[(1,4,76)]:
            row=events[pos];pos+=1;values=row[7].split(',')
            key=list(map(float,values[:12]))
            assert row[6]=='case' and len(values)==112
            assert key==[len(result),tx,pattern,kind,left,right,SX,SY,tx,4,0,0.8]
            result.append({'key':key,'pixels':unpack(list(map(int,values[12:])))})
    assert pos==len(events)-1
    return result,input_exact


def old_mode(tx,y,x,left,right,scalar):
    if scalar:return 'byte'
    yy=coordinates(SY,0,4,0,y)[1]-.8
    start=max(left,math.ceil(tx));end=min(right,math.floor(tx+60*SX))
    chunk=start+(x-start)//256*256;stop=min(end,chunk+256)
    if not 1<=yy<57:return 'byte'
    while chunk<stop and coordinates(SX,tx,0,chunk,0)[0]<1:chunk+=1
    while stop>chunk and coordinates(SX,tx,0,stop-1,0)[0]>=59:stop-=1
    return 'vertical' if chunk<=x<chunk+(stop-chunk)//4*4 else 'byte'


def analyze(native):
    cases,input_exact=decode(native)
    score={'samples':0,'exact':0,'failures':[]};groups=defaultdict(dict);overlaps=defaultdict(set);fringes=[]
    excluded=0
    for case in cases:
        i,tx,pattern,kind,left,right,*_=case['key'];pattern=int(pattern)
        for index,(y,x) in enumerate(itertools.product(YS,range(70,80))):
            p=case['pixels'][index]
            inside=bool(kind) or left<=x<right
            if not inside or x+1>tx+60*SX:
                excluded+=1
                fringes.append({'case':int(i),'x':x,'y':y,'native':p,'clip_included':inside})
                continue
            assert p[3]==255
            xx=coordinates(SX,tx,0,x,0)[0];yy=coordinates(SY,0,4,0,y)[1]-.8
            mode=old_mode(tx,y,x,int(left),int(right),bool(kind))
            predicted=sample(xx,yy,lambda a,b:texel(pattern,a,b),mode)+[255]
            score['samples']+=1
            if p==predicted:score['exact']+=1
            else:score['failures'].append({'case':int(i),'x':x,'y':y,'old_mode':mode,'actual':predicted,'native':p})
            groups[(tx,int(kind),int(left),int(right),x,y)][pattern]=p[0]
            overlaps[(tx,pattern,x,y)].add(tuple(p))
    compatibility=[]
    for key,values in groups.items():
        assert set(values)==set(range(6))
        tx,kind,left,right,x,y=key;xx=coordinates(SX,tx,0,x,0)[0];yy=coordinates(SY,0,4,0,y)[1]-.8
        compatible=[]
        for mode in ('byte','vertical','horizontal'):
            signature=[sample(xx,yy,lambda a,b:texel(pattern,a,b),mode)[0] for pattern in range(6)]
            if signature==[values[p] for p in range(6)]:compatible.append(mode)
        compatibility.append({'key':list(key),'red_responses':[values[p] for p in range(6)],'compatible_modes':compatible,
                              'old_mode':old_mode(tx,y,x,left,right,bool(kind))})
    return {'input_exact':input_exact,'cases':len(cases),'interior_old_model':score,
            'coordinate_compatible_groups':sum(bool(r['compatible_modes']) for r in compatibility),'groups':len(compatibility),
            'mode_compatibility':compatibility,'clip_dependent_overlap_groups':sum(len(v)>1 for v in overlaps.values()),
            'overlap_groups':len(overlaps),'excluded_fringe_or_clipped_samples':excluded,'fringe_readbacks':fringes,
            'routing_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();r=analyze(args.native);args.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print({k:v for k,v in r.items() if k not in ('mode_compatibility','fringe_readbacks','interior_old_model')})
    print({k:v for k,v in r['interior_old_model'].items() if k!='failures'})
