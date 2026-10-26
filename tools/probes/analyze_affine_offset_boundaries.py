"""Compare norm-offset quantization at independently selected integer boundaries."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_affine_footprint import floor_surd
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_negative_terms import indices
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.generate_affine_offset_boundaries import select
from tools.probes.run_nested_filters import unpack


def analyze(native, selection_native):
    selected=select(selection_native);assert len(selected)==5
    source=[];samples=[]
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='source':
            assert int(v[0])==len(source)//128 and len(v)==257
            source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='sample':
            assert len(v)==20 and int(v[0])==len(samples)
            samples.append((v[:18],unpack(list(map(int,v[18:])))[0]))
        else:assert [kind,payload]==['done','ok']
    assert source==[[x,y,73,255] for y in range(128) for x in range(128)] and len(samples)==45
    scores={};rows=[]
    for k,pixel in samples:
        case,dx,dy=map(int,k[1:4]);assert -1<=dx<=1 and -1<=dy<=1
        ref=selected[case];assert list(map(Fraction,k[4:16]))==list(map(Fraction,ref['key'][5:17]))
        x,y=map(int,k[16:18]);assert (x,y)==(ref['x']+dx,ref['y']+dy)
        co=inverse_signed(ref['key']);predictions={'exact_norm':indices(co,x,y,'negative_minimum')}
        floor_values=[];round_values=[]
        for row in co:
            a,b,t=[math.floor(v*65536+Fraction(1,2)) for v in row]
            minimum=min(0,a,b);square=Fraction(a*a+b*b,4)
            floored=floor_surd(Fraction(minimum),square)
            rounded=floor_surd(Fraction(minimum)+Fraction(1,2),square)
            floor_values.append((a*x+b*y+t+floored)//65536)
            round_values.append((a*x+b*y+t+rounded)//65536)
        predictions['floor_offset']=floor_values;predictions['round_offset']=round_values
        assert predictions['exact_norm']==floor_values
        for family,result in predictions.items():
            actual=result+[73,255];s=scores.setdefault(family,{'samples':0,'exact':0,'centers':0,'centers_exact':0,'max_source_index_delta':0,'failures':[]})
            s['samples']+=1;s['exact']+=actual==pixel;s['centers']+=dx==dy==0;s['centers_exact']+=dx==dy==0 and actual==pixel
            s['max_source_index_delta']=max(s['max_source_index_delta'],max(abs(a-b) for a,b in zip(actual,pixel)))
            if actual!=pixel:s['failures'].append({'key':k,'actual':actual,'native':pixel})
        rows.append({'key':k,'predictions':predictions,'native':pixel})
    return {'source_texels_exact':16384,'selected_before_native_rgb':selected,'samples':45,'scores':scores,'rows':rows,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--selection-native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native,a.selection_native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],'centers',v['centers_exact'],v['centers'])
