"""Retain authored inner translation and fill metadata in the second source-cache binding."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
from PIL import Image
from tools.probes.build_bound_bitmap_component import source_tags,bitmap_shape_fill_polygons,ROOT
from tools.probes.inventory_bitmap_roundtrip import decode_lossless
from tools.probes.analyze_component_shape_identity import analyze as validate_authored
from tools.probes.analyze_component_cache_boundaries import decode
from tools.probes.analyze_bitmap_cache_support_grid import separate_bounds
from tools.probes.analyze_cache_device_origin import device_translation
from tools.probes.bound_bitmap_candidate import render_leaf
from tools.probes.analyze_jiraiya_filter_boundary import comparison
from tools.probes.analyze_blur_kernel_heldout import render as blur


def source_leaf():
    native=ROOT/'evidence/importer-loud-fail/r125/native';validate_authored(native)
    shape=ET.parse(native/'authored-shape.xml').getroot()
    wrapper=ET.parse(native/'authored-wrapper.xml').getroot()
    fill=shape.find('.//fillStyles/item');fm=fill.find('bitmapMatrix')
    matrix=wrapper.find('./subTags/item[@type="PlaceObject2Tag"]/matrix')
    assert not shape.findall('.//lineStyles/item')
    assert matrix.get('hasRotate')=='false' and matrix.get('hasScale')=='false'
    raw=next(p for c,p,r in source_tags(ROOT/'game/fighter/jiraiya.swf') if c==36 and struct.unpack_from('<H',p)[0]==166)
    _,width,height,pixels=decode_lossless(raw)
    return {'source':'game/fighter/jiraiya.swf','shape_id':276,'bitmap_id':166,'width':width,'height':height,
            'fill_matrix':dict(fm.attrib),'fill':dict(fill.attrib),'fill_masks':bitmap_shape_fill_polygons(shape),
            'pixels_premultiplied':pixels,'inner_matrix':dict(matrix.attrib),'production_admitted':False}


def render_cache(leaf,properties,placement):
    _,_,dsx,dsy,dx,dy,observed_sx,observed_sy,tx,ty,*_=properties
    assert dsx==dsy==1
    sx=round(placement['scaleX']*65536)/65536;sy=round(placement['scaleY']*65536)/65536
    assert float(format(sx,'.15g'))==observed_sx and float(format(sy,'.15g'))==observed_sy
    fx=float(leaf['fill_matrix']['translateX'])/20;fy=float(leaf['fill_matrix']['translateY'])/20
    ix=float(leaf['inner_matrix']['translateX'])/20;iy=float(leaf['inner_matrix']['translateY'])/20
    xb=separate_bounds(fx+ix,leaf['width'],sx,tx,dx)
    yb=separate_bounds(fy+iy,leaf['height'],sy,ty,dy)
    transform={'sx':sx,'sy':sy,
               'tx':device_translation(sx,tx,dx,xb[0])+round(ix*sx*4)/4,
               'ty':device_translation(sy,ty,dy,yb[0])+round(iy*sy*4)/4}
    width,height=xb[1]-xb[0],yb[1]-yb[0]
    local=render_leaf(leaf,transform,(width,height));actual=[[0]*4 for _ in range(240000)]
    assert 0<=xb[0]<xb[1]<=600 and 0<=yb[0]<yb[1]<=400
    for y in range(height):
        for x in range(width):actual[(yb[0]+y)*600+xb[0]+x]=local[y*width+x]
    return actual,{'x_bounds':xb,'y_bounds':yb,'local_transform':transform,'local_size':[width,height]}


def analyze(output=None):
    leaf=source_leaf();build,images,matrices,_,_=decode(ROOT/'evidence/importer-loud-fail/r124/native')
    scores={};metadata=[];pinned=[]
    if output:output.mkdir(parents=True,exist_ok=True)
    for i,properties in enumerate(matrices):
        actual,info=render_cache(leaf,properties,build['case']['placement']['matrix']);metadata.append(info)
        channels=[]
        for channel in range(4):
            image=[[actual[y*600+x][channel] for x in range(600)] for y in range(400)]
            filtered=blur(image,0.,15.,1,'grouped');channels.append([v for row in filtered for v in row])
        filtered=[list(v) for v in zip(*channels)]
        for kind,pixels in [('cache',actual),('authored',filtered)]:
            scores[f'{i}-{kind}']=comparison(pixels,images[f'{i}-{kind}'])
            if output:Image.frombytes('RGBA',(600,400),bytes(v for p in pixels for v in p)).save(output/f'{i}-{kind}.png')
        if i==1:
            composed=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in filtered]
            for tick in (0,3):
                path=ROOT/f'evidence/importer-loud-fail/r21/components/jiraiya/jiraiya-342-766-29-{tick:03d}.native.png'
                target=list(Image.open(path).convert('RGBA').getdata())
                pinned.append({'tick':tick,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(composed,target)})
    return {'metadata':metadata,'comparisons':scores,'pinned_comparisons':pinned,'authored_inner_matrix':leaf['inner_matrix'],'authored_fill_matrix':leaf['fill_matrix'],
            'source_derived_cpu_component_exact':all(v['exact']==v['samples'] for v in list(scores.values())+pinned),'gpu_binding_verified':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=analyze(args.output);(args.output/'analysis.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    for name,v in result['comparisons'].items():print(name,v['exact'],v['samples'],v['max_channel_delta'])
    print('pinned',[(v['exact'],v['samples']) for v in result['pinned_comparisons']])
