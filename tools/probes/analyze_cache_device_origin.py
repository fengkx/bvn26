"""Test one device-space origin construction against every retained cache-origin family."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_origin import decode as origin_cases
from tools.probes.analyze_bitmap_cache_width import decode as width_cases, ROOT
from tools.probes.analyze_cache_affine_candidate import controls, f32
from tools.probes.analyze_clipped_half_step import axis


def cases():
    for suite,count,width in [('r101',378,600),('r102',1152,1200)]:
        for c in origin_cases(ROOT/f'evidence/importer-loud-fail/{suite}/native',count,width):
            i,minimum,_,_,outer,scale,inner,bmin,_=c['key']
            yield suite,int(i),scale,inner,outer,bmin,minimum,60,60,c['cached']
    rows,_=width_cases(ROOT/'evidence/importer-loud-fail/r103/native')
    for c in rows:
        i,_,_,source_width,_,_,outer,scale,inner,bmin,_,painted=c['key']
        yield 'r103',int(i),scale,inner,outer,bmin,0,int(source_width),painted,c['cached']
    for suite,i,scale,inner,outer,bmin,actual in controls():
        yield suite,i,scale,inner,outer,bmin,0,16,16,actual


def raster_sample(scale,translation,pixel,minimum,width):
    q=axis(scale,translation,pixel,'even')-minimum
    index=math.floor(q);fraction=math.floor((q-index)*256)
    def texel(x):
        x=max(0,min(width-1,x));return [x%2*255,(x*37+17)%256,113]
    a,b=texel(index),texel(index+1)
    return [(x*(256-fraction)+y*fraction)//256 for x,y in zip(a,b)]


def device_translation(scale,inner,outer,origin):
    # 0x3d4ccccd is independently read from the native binary, not fitted to RGB.
    device_scale=f32(f32(4*f32(0.05))*f32(scale))
    local_origin=-round(f32(f32(origin*4)*f32(1/device_scale)))
    return (round(f32(f32(local_origin)*device_scale))+round(inner*4)+math.trunc(outer*4))/4


def analyze():
    scores={};per_case=[]
    for suite,i,scale,inner,outer,bmin,minimum,width,painted,actual in cases():
        effective=round(inner*4)/4+math.trunc(outer*4)/4
        consumed_origin=math.floor(bmin-inner+effective)
        authored_origin=math.floor(bmin+outer)
        methods={
            'baseline':(consumed_origin,effective-consumed_origin),
            'device_consumed_bounds':(consumed_origin,device_translation(scale,inner,outer,consumed_origin)),
            'device_authored_bounds':(authored_origin,device_translation(scale,inner,outer,authored_origin)),
        }
        positions=[x for x in range(len(actual)) if (minimum+1)*scale+effective<=x and x+1<=(minimum+painted-1)*scale+effective]
        for method,(origin,translation) in methods.items():
            score=scores.setdefault(suite+'/'+method,{'samples':0,'exact':0,'max_channel_delta':0,'counterexamples':[]})
            failures=0
            for x in positions:
                predicted=raster_sample(scale,translation,x-origin,minimum,width)
                score['samples']+=1
                if predicted==actual[x]:score['exact']+=1
                else:
                    failures+=1;delta=max(abs(a-b) for a,b in zip(predicted,actual[x]));score['max_channel_delta']=max(score['max_channel_delta'],delta)
                    if len(score['counterexamples'])<16:score['counterexamples'].append({'case':i,'x':x,'origin':origin,'local_translation':translation,'predicted':predicted,'native':actual[x]})
            per_case.append({'suite':suite,'case':i,'method':method,'samples':len(positions),'different_pixels':failures})
    return {'comparisons':scores,'cases':per_case,'specific_normalization_branch_verified':False,'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze();a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['comparisons'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
