"""Independently discriminate half-step rounding on scalar clipped bitmap samples."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_blur_kernel_heldout import ROOT
from tools.probes.run_nested_filters import unpack

SCALES=(1.23333740234375,3,5,7,1.24481201171875,2)
ORIGINS=(0,1,4,15,-4)


def axis(scale,translation,pixel,rule):
    inverse=math.floor(65536/scale+.5)
    half={'ceiling':(inverse+1)//2,'even':round(inverse/2),'floor':inverse//2}[rule]
    quarter=math.trunc(translation*4)/4
    return (pixel*inverse+math.floor(-quarter/scale*65536+.5)+half-32768)/65536


def texel(x):return [x%2*255,(x*37+17)%256,113]


def decode(native):
    build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    events=[s.split('|') for s in (native/'native.log').read_text().splitlines() if s.startswith('AIREF|')]
    assert len(events)==77 and events[-1][6:]==['done','ok']
    for i,row in enumerate(events):assert row[1]==build['run_id'] and row[2:6]==[str(i),'0','0','0']
    pos=0;cases=[];inputs=0
    for width in (60,256):
        for y in range(8):
            row=events[pos];pos+=1;v=list(map(int,row[7].split(',')))
            assert row[6]=='source' and v[:2]==[width,y] and len(v)==width+2
            for x,p in enumerate(v[2:]):
                p&=0xffffffff;assert [(p>>s)&255 for s in (16,8,0)]==texel(x) and p>>24==255;inputs+=1
        for scale in SCALES:
            for origin in ORIGINS:
                row=events[pos];pos+=1;v=row[7].split(',');key=list(map(float,v[:8]))
                assert row[6]=='case' and len(v)==776
                assert key==[len(cases),width,scale,origin,scale,1,origin,0]
                cases.append({'key':key,'pixels':unpack(list(map(int,v[8:])))})
    return cases,inputs


def analyze(native):
    cases,inputs=decode(native)
    scores={rule:{'samples':0,'exact':0,'failures':[]} for rule in ('ceiling','even','floor')}
    excluded=[]
    for case in cases:
        i,width,scale,origin,*_=case['key'];width=int(width)
        for x,target in enumerate(case['pixels']):
            if x<origin or x+1>origin+width*scale:
                excluded.append({'case':int(i),'x':x,'native':target})
                continue
            assert target[3]==255
            for rule,score in scores.items():
                q=axis(scale,origin,x,rule);base=math.floor(q);f=math.floor((q-base)*256)
                a,b=[texel(max(0,min(width-1,j))) for j in (base,base+1)]
                predicted=[(v*(256-f)+w*f)//256 for v,w in zip(a,b)]+[255]
                score['samples']+=1
                if predicted==target:score['exact']+=1
                else:score['failures'].append({'case':int(i),'width':width,'scale':scale,'origin':origin,'x':x,
                    'inverse':math.floor(65536/scale+.5),'actual':predicted,'native':target})
    return {'input_exact':inputs,'scores':scores,'excluded_fringe_or_outside':excluded,
            'passed_scalar_rules':[r for r,s in scores.items() if not s['failures']],
            'global_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();r=analyze(args.native);args.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print({k:(s['exact'],s['samples']) for k,s in r['scores'].items()});print(r['passed_scalar_rules'])
