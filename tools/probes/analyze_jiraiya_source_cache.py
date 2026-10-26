"""Render the original Jiraiya cache and authored blur from source texels and geometry."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_jiraiya_bitmap_binding import decode as leaf_reference
from tools.probes.analyze_jiraiya_cache_boundary import decode as native_reference
from tools.probes.analyze_bitmap_cache_support_grid import separate_bounds
from tools.probes.analyze_cache_device_origin import device_translation
from tools.probes.bound_bitmap_candidate import render_leaf
from tools.probes.analyze_jiraiya_filter_boundary import comparison,ROOT
from tools.probes.analyze_jiraiya_materialized_blur import integer_blur


def render_cache(leaf,properties):
    _,_,sx,sy,tx,ty,inner_sx,inner_sy,inner_tx,inner_ty,*_=properties
    fx=float(leaf['fill_matrix']['translateX'])/20
    fy=float(leaf['fill_matrix']['translateY'])/20
    xb=separate_bounds(fx,leaf['width'],sx*inner_sx,inner_tx*sx,tx)
    yb=separate_bounds(fy,leaf['height'],sy*inner_sy,inner_ty*sy,ty)
    transform={'sx':sx*inner_sx,'sy':sy*inner_sy,
               'tx':device_translation(sx*inner_sx,inner_tx*sx,tx,xb[0]),
               'ty':device_translation(sy*inner_sy,inner_ty*sy,ty,yb[0])}
    width,height=xb[1]-xb[0],yb[1]-yb[0]
    local=render_leaf(leaf,transform,(width,height))
    output=[[0]*4 for _ in range(600*400)]
    for y in range(height):
        for x in range(width):
            if 0<=xb[0]+x<600 and 0<=yb[0]+y<400:
                output[(yb[0]+y)*600+xb[0]+x]=local[y*width+x]
    return output,{'x_bounds':xb,'y_bounds':yb,'local_transform':transform,'local_size':[width,height]}


def analyze(output=None):
    leaf,_=leaf_reference(ROOT/'evidence/importer-loud-fail/r89/native')
    images,_,_=native_reference(ROOT/'evidence/importer-loud-fail/r100/native')
    reference=ROOT/'evidence/importer-loud-fail/r99';pins=json.loads((reference/'provenance.json').read_text())
    path=reference/'analysis.json.gz'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==pins['evidence_sha256']['analysis.json.gz']
    properties=json.loads(gzip.decompress(path.read_bytes()))['properties']
    comparisons={};metadata=[]
    if output:output.mkdir(parents=True,exist_ok=True)
    for index,property_index in enumerate((0,3,6)):
        pixels,info=render_cache(leaf,properties[property_index]);metadata.append(info)
        blurred=integer_blur(pixels)
        for name,actual,target in [('cache',pixels,images[f'{index}-cache']),('authored',blurred,images[f'{index}-authored'])]:
            comparisons[f'{index}-{name}']=comparison(actual,target)
            if output:Image.frombytes('RGBA',(600,400),bytes(c for p in actual for c in p)).save(output/f'{index}-{name}.png')
    return {'metadata':metadata,'comparisons':comparisons,'source_derived_cpu_component_exact':all(v['exact']==v['samples'] for v in comparisons.values()),
            'gpu_binding_verified':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=analyze(args.output)
    (args.output/'analysis.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    for name,v in result['comparisons'].items():print(name,v['exact'],v['samples'],v['max_channel_delta'])
