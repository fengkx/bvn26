"""Compare fixed fractional-weight precisions on independent indexed/32-bit native controls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_clipped_half_step import axis
from tools.probes.bitmap_half_even_candidate import interpolate
from tools.probes.run_nested_filters import unpack
from tools.probes.build_bound_bitmap_component import ROOT


def decode(native):
    build=json.loads((native/'build.json').read_text());assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    records=events(native);assert len(records)==1218;source=[];samples=[]
    for kind,payload in records:
        v=payload.split(',')
        if kind=='source':
            assert len(v)==71 and int(v[0])==len(source)//35;source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='sample':
            assert len(v)==16;key=list(map(float,v[:13]));assert int(key[0])==len(samples) and v[13]=='false';assert key[12]==(1 if key[1]==0 else 0)
            samples.append({'key':key,'native':unpack(list(map(int,v[14:])))[0]})
        else:assert [kind,payload]==['done','ok']
    expected=[[16+24*(x%8),16+24*(y%8),73,255] for y in range(65) for x in range(35)]
    assert source==expected and hashlib.sha256(bytes(c for p in source for c in p)).hexdigest()==build['synthetic_source']['raw_rgba_sha256']
    assert len(samples)==1152 and all(p['native'][3]==255 for p in samples)
    for a,b in zip(samples[::2],samples[1::2]):assert a['key'][1]==0 and b['key'][1]==1 and a['key'][2:12]==b['key'][2:12]
    return source,samples


def analyze(native):
    source,samples=decode(native);scores={};texel=lambda x,y:source[max(0,min(64,y))*35+max(0,min(34,x))]
    for sample in samples:
        _,api,fx,fy,sx,sy,cx,cy,dx,dy,x,y,_=sample['key'];assert fx==16.6 and fy==-8.15 and sx==sy
        tx=round(cx*4)/4+math.trunc(dx*4)/4;ty=round(cy*4)/4+math.trunc(dy*4)/4
        u,v=axis(sx,tx,x,'even')-fx,axis(sy,ty,y,'even')-fy
        for bits in (4,5,6,8):
            steps=1<<bits;uv=[math.floor(q)+math.floor((q-math.floor(q))*steps)/steps for q in (u,v)]
            actual=interpolate(*uv,texel,'byte');score=scores.setdefault(f'api{int(api)}-bits{bits}',{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]})
            score['samples']+=1;score['exact']+=actual==sample['native'];score['max_channel_delta']=max(score['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,sample['native'])))
            if actual!=sample['native']:score['failures'].append({**sample,'unquantized_uv':[u,v],'weight_uv':uv,'actual':actual})
    return {'source_pixels_exact':len(source),'samples':samples,'scores':scores,'indexed_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
