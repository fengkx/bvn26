"""Validate the header-only control and require native indexed texels before scalar arithmetic."""
import argparse
import json
import math
from pathlib import Path
from tools.probes.analyze_indexed_bitmap_readback import analyze as readback
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_clipped_half_step import axis
from tools.probes.bitmap_half_even_candidate import interpolate
from tools.probes.run_nested_filters import unpack


def analyze(native):
    build=json.loads((native/'build.json').read_text());proof=build['header_intervention']
    assert proof['before_header_bytes']==2 and proof['after_header_bytes']==6 and proof['payload_bytes']==55 and proof['other_tags_byte_identical'] and proof['other_tag_count']==647
    assert proof['payload_sha256']==build['indexed_export']['bitmap_payload_sha256']
    result=readback(native);assert result['native_indexed_source_verified']
    palette=[[0,0,0,0],[255,0,0,255],[0,255,0,255],[0,0,255,255]]
    texel=lambda x,y:palette[max(0,min(64,y))%2*2+max(0,min(34,x))%2]
    scores={str(i):{'samples':0,'exact':0,'failures':[]} for i in (0,1)}
    for kind,payload in events(native):
        if kind not in ('sample0','sample1'):continue
        v=payload.split(',');key=list(map(float,v[:13]));_,api,fx,fy,sx,sy,cx,cy,dx,dy,x,y,_=key
        u=axis(sx,round(cx*4)/4+math.trunc(dx*4)/4,x,'even')-fx
        w=axis(sy,round(cy*4)/4+math.trunc(dy*4)/4,y,'even')-fy
        actual=interpolate(u,w,texel,'byte');target=unpack(list(map(int,v[14:])))[0];score=scores[str(int(api))];score['samples']+=1;score['exact']+=actual==target
        if actual!=target:score['failures'].append({'key':key,'actual':actual,'native':target})
    return {'header_intervention':proof,'readback':result,'fixed_eight_bit_scalar':scores,'indexed_continuous_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print([(k,v['exact'],v['samples']) for k,v in r['fixed_eight_bit_scalar'].items()])
