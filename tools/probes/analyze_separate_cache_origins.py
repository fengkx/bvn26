"""Apply independently measured separate geometry/translation origins to retained cache suites."""
import argparse
import json
import math
from pathlib import Path
from tools.probes.analyze_cache_device_origin import ROOT,cases,device_translation,raster_sample
from tools.probes.analyze_bitmap_cache_support_grid import separate_bounds
from tools.probes.analyze_bitmap_cache_left_bounds import analyze as left_bounds
from tools.probes.analyze_bitmap_cache_fill_bounds import analyze as fill_bounds


def controls():
    left={int(c['key'][0]):c['key'][1] for c in left_bounds(ROOT/'evidence/importer-loud-fail/r109/native')['cases']}
    for suite,i,scale,inner,outer,bmin,fill,width,painted,actual in cases():
        minimum=left[i] if suite=='r109' else fill
        effective=round(inner*4)/4+math.trunc(outer*4)/4
        positions=[x for x in range(len(actual)) if (fill+1)*scale+effective<=x and x+1<=(fill+painted-1)*scale+effective]
        yield suite,i,minimum,scale,inner,outer,fill,width,actual,positions
    for c in fill_bounds(ROOT/'evidence/importer-loud-fail/r113/native')['cases']:
        i,mode,value,minimum,maximum,fill,_,_,scale,inner,outer,bmin,_=c['key']
        effective=round(inner*4)/4+math.trunc(outer*4)/4
        positions=[x for x in range(800) if effective+3*scale<=x and x+1<=effective+55*scale]
        yield 'r113/mode'+str(int(mode)),int(i),minimum,scale,inner,outer,fill,60,c['cached'],positions


def analyze():
    scores={};per_case=[]
    for suite,i,minimum,scale,inner,outer,fill,width,actual,positions in controls():
        consumed_minimum=math.trunc(minimum*20)/20
        origin=separate_bounds(consumed_minimum,0,scale,inner,outer)[0]
        translation=device_translation(scale,inner,outer,origin)
        score=scores.setdefault(suite,{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]})
        count=0
        for x in positions:
            predicted=raster_sample(scale,translation,x-origin,fill,width)
            score['samples']+=1
            if predicted==actual[x]:score['exact']+=1
            else:
                count+=1
                score['max_channel_delta']=max(score['max_channel_delta'],max(abs(a-b) for a,b in zip(predicted,actual[x])))
                score['failures'].append({'case':i,'x':x,'origin':origin,'translation':translation,'predicted':predicted,'native':actual[x]})
        per_case.append({'suite':suite,'case':i,'minimum':minimum,'scale':scale,'inner':inner,'outer':outer,'origin':origin,'samples':len(positions),'different_pixels':count})
    return {'comparisons':scores,'cases':per_case,'source_cache_initializer_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze();a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for name,v in r['comparisons'].items():print(name,v['exact'],v['samples'],v['max_channel_delta'])
