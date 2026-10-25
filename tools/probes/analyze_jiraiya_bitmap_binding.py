"""Measure source-backed fractional fill binding without admitting coverage or matrix composition."""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
from tools.probes.build_bound_bitmap_component import ROOT, source_tags
from tools.probes.inventory_bitmap_roundtrip import decode_lossless
from tools.probes.bitmap_sampling_candidate import coordinates, interpolate
from tools.probes.run_nested_filters import unpack


def decode(native):
    fixture=json.loads((native/'fixture.json').read_text());build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest()==build['fixture_sha256']
    assert fixture['production_admitted'] is False
    assert hashlib.sha256((ROOT/fixture['source']).read_bytes()).hexdigest()==fixture['source_sha256']==build['source_sha256']
    raw={struct.unpack_from('<H',p)[0]:(p,r) for c,p,r in source_tags(ROOT/fixture['source']) if c in (2,36) and struct.unpack_from('<H',p)[0] in (273,274)}
    assert {str(k):hashlib.sha256(r).hexdigest() for k,(_,r) in raw.items()}==fixture['raw_tag_sha256']
    assert decode_lossless(raw[273][0])[3]==fixture['pixels_premultiplied']
    path=native/'native.log';text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    events=[s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    w,h=fixture['target_size'];assert len(events)==len(fixture['cases'])*(h+1)+1 and events[-1][6:]==['done','ok']
    for i,row in enumerate(events):assert row[1]==build['run_id'] and row[2:6]==[str(i),'0','0','0']
    images=[]
    for i,case in enumerate(fixture['cases']):
        block=events[i*(h+1):(i+1)*(h+1)]
        assert block[0][6]=='case'
        assert list(map(float,block[0][7].split(',')))==[i,*[float(format(case[k],'.15g')) for k in ('sx','sy','tx','ty')]]
        image=[]
        for y,row in enumerate(block[1:]):
            values=row[7].split(',');assert row[6]=='row' and values[:2]==[str(i),str(y)] and len(values)==2+w*2
            image.extend(unpack(list(map(int,values[2:]))))
        images.append(image)
    return fixture,images


def render(fixture,case,model):
    w,h=fixture['target_size'];sw,sh=fixture['width'],fixture['height'];raw=fixture['pixels_premultiplied']
    sx,sy,tx,ty=[Fraction(str(case[k])) for k in ('sx','sy','tx','ty')]
    left,right=tx,tx+sw*sx;top,bottom=ty+Fraction(4,5)*sy,ty+Fraction(294,5)*sy
    result=[[0]*4 for _ in range(w*h)];regions=['outside']*(w*h)
    full_left=max(0,math.ceil(left));full_right=min(w,math.floor(right))
    def texel(x,y):return raw[max(0,min(sh-1,y))*sw+max(0,min(sw-1,x))]
    xs={x:coordinates(float(sx),float(tx),0,x,0)[0] for x in range(max(0,math.floor(left)),min(w,math.ceil(right)))}
    for y in range(max(0,math.floor(top)),min(h,math.ceil(bottom))):
        if model=='compose_before_quantization':
            yy=coordinates(float(sy),0,float(top),0,y)[1]
        elif model=='inverse_draw_then_fill':
            yy=coordinates(float(sy),0,float(ty),0,y)[1]-0.8
        else:raise ValueError('Unknown fixed matrix construction')
        modes={x:True for x in xs}
        if 1 <= yy < sh-1:
            for chunk in range(full_left,full_right,256):
                start,end=chunk,min(full_right,chunk+256)
                while start<end and xs[start]<1:start+=1
                while end>start and xs[end-1]>=sw-1:end-=1
                for x in range(start,start+(end-start)//4*4):modes[x]=False
        for x,xx in xs.items():
            coverage=(min(Fraction(x+1),right)-max(Fraction(x),left))*(min(Fraction(y+1),bottom)-max(Fraction(y),top))
            assert 0 < coverage <= 1
            rgb=interpolate(xx,yy,texel,byte_weights=modes[x])
            alpha=interpolate(xx,yy,lambda a,b:[texel(a,b)[3]]*3,byte_weights=modes[x])[0]
            result[y*w+x]=[math.floor(c*coverage) for c in (*rgb,alpha)]
            regions[y*w+x]='interior' if coverage==1 else 'fringe'
    return result,regions


def analyze(native):
    fixture,images=decode(native);scores={}
    for model in ('compose_before_quantization','inverse_draw_then_fill'):
        cases=[]
        for i,(case,target) in enumerate(zip(fixture['cases'],images)):
            actual,regions=render(fixture,case,model)
            parts={k:{'samples':0,'exact':0,'max_delta':0,'native_nonzero_alpha':0} for k in ('outside','interior','fringe')};failures=[]
            for index,(p,q,region) in enumerate(zip(actual,target,regions)):
                score=parts[region];score['samples']+=1;score['native_nonzero_alpha']+=q[3]>0;delta=max(abs(a-b) for a,b in zip(p,q));score['max_delta']=max(score['max_delta'],delta)
                if delta:failures.append({'x':index%384,'y':index//384,'region':region,'actual':p,'native':q})
                else:score['exact']+=1
            cases.append({'case':i,'transform':case,'regions':parts,'exact_image':not failures,'failures':failures})
        scores[model]={'cases':cases,'exact_images':sum(c['exact_image'] for c in cases)}
    return {'scores':scores,'source_texels_exact':3480,'whole_image_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();r=analyze(args.native);args.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print({k:[c['regions'] for c in v['cases']] for k,v in r['scores'].items()})
