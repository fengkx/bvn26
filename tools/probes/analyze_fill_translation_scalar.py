"""Discriminate fill-matrix translation consumption on fixed single-pixel native controls."""
import argparse
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_clipped_half_step import axis
from tools.probes.bitmap_half_even_candidate import interpolate


def analyze(native):
    records=events(native);assert len(records)==1161
    source=[];samples=[]
    for kind,payload in records:
        values=payload.split(',')
        if kind=='source':
            assert int(values[0])==len(source)//8 and len(values)==17
            source.extend(unpack(list(map(int,values[1:]))))
        elif kind=='sample':
            key=list(map(float,values[:13]));assert int(key[0])==len(samples) and key[1:3]==[1,1] and key[11:]==[1,1]
            actual=unpack(list(map(int,values[13:])));assert len(actual)==1;samples.append({'key':key,'native':actual[0]})
        else:assert [kind,payload]==['done','ok']
    assert source==[[16+24*x,16+24*y,73,255] for y in range(8) for x in range(8)] and len(samples)==1152
    texel=lambda x,y:source[max(0,min(7,y))*8+max(0,min(7,x))]
    scores={name:{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]} for name in ('subtract_after_fixed_inverse','compose_before_fixed_translation','consume_fill_twips_then_compose')}
    for item in samples:
        _,_,_,fx,fy,sx,sy,tx,ty,x,y,_,_=item['key'];assert sx==sy and tx==8 and ty==6
        coords={}
        coords['subtract_after_fixed_inverse']=[axis(sx,tx,x,'even')-fx,axis(sy,ty,y,'even')-fy]
        for name in ('compose_before_fixed_translation','consume_fill_twips_then_compose'):
            uv=[]
            for s,t,p,f in ((sx,tx,x,fx),(sy,ty,y,fy)):
                if name=='consume_fill_twips_then_compose':f=math.trunc(f*20)/20
                inverse=math.floor(65536/s+.5)
                uv.append((p*inverse+math.floor((-t/s-f)*65536+.5)+round(inverse/2)-32768)/65536)
            coords[name]=uv
        for name,uv in coords.items():
            actual=interpolate(*uv,texel,'byte');score=scores[name];score['samples']+=1;score['exact']+=actual==item['native'];score['max_channel_delta']=max(score['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,item['native'])))
            if actual!=item['native']:score['failures'].append({**item,'uv':uv,'actual':actual})
    return {'source_pixels':source,'native_samples':samples,'scores':scores,'fill_translation_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
