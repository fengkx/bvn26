"""Source-driven bounded rectangle cache and Blur comparison with original native images."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT,source_tags,bitmap_shape_fill_polygons
from tools.probes.inventory_bitmap_roundtrip import decode_lossless
from tools.probes.rect_mask_binding import canonical_rect_mask,render_rect
from tools.probes.analyze_component_cache_boundaries import decode
from tools.probes.analyze_bitmap_cache_support_grid import separate_bounds
from tools.probes.analyze_cache_device_origin import device_translation
from tools.probes.analyze_blur_kernel_heldout import render as blur
from tools.probes.analyze_jiraiya_filter_boundary import comparison


def load_fixture(folder):
    path=folder/'fixture.json';build=json.loads((folder/'build.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==build['fixture_sha256']
    leaf=json.loads(path.read_text());assert not leaf['production_admitted']
    source=ROOT/leaf['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==leaf['source_sha256']
    ids=(leaf['bitmap_id'],leaf['shape_id'],leaf['case']['symbol'])
    raw={str(struct.unpack_from('<H',p)[0]):(p,r) for code,p,r in source_tags(source) if code in (2,36,39) and struct.unpack_from('<H',p)[0] in ids}
    assert {k:hashlib.sha256(r).hexdigest() for k,(_,r) in raw.items()}==leaf['raw_tag_sha256']
    cid,width,height,pixels=decode_lossless(raw[str(leaf['bitmap_id'])][0])
    assert [cid,width,height]==[leaf['bitmap_id'],leaf['width'],leaf['height']] and pixels==leaf['pixels_premultiplied']
    shape=ET.fromstring(leaf['shape_xml']);fill=shape.find('.//fillStyles/item')
    assert dict(fill.attrib)==leaf['fill'] and dict(fill.find('bitmapMatrix').attrib)==leaf['fill_matrix']
    assert bitmap_shape_fill_polygons(shape)==leaf['fill_masks'];canonical_rect_mask(leaf)
    wrapper=ET.fromstring(leaf['wrapper_xml']);placements=wrapper.findall('./subTags/item[@type="PlaceObject2Tag"]')
    assert len(placements)==1 and dict(placements[0].find('matrix').attrib)==leaf['inner_matrix']
    return leaf


def render_cache(leaf,properties):
    _,_,dsx,dsy,dx,dy,observed_sx,observed_sy,tx,ty,*_=properties
    if dsx!=1 or dsy!=1:raise ValueError('Outer scale outside bounded source cache domain')
    placement=leaf['case']['placement']['matrix']
    if placement.get('hasRotate')=='true':raise ValueError('Outer affine outside bounded source cache domain')
    sx=round(placement.get('scaleX',1)*65536)/65536;sy=round(placement.get('scaleY',1)*65536)/65536
    assert float(format(sx,'.15g'))==observed_sx and float(format(sy,'.15g'))==observed_sy
    fx=float(leaf['fill_matrix']['translateX'])/20;fy=float(leaf['fill_matrix']['translateY'])/20
    ix=float(leaf['inner_matrix']['translateX'])/20;iy=float(leaf['inner_matrix']['translateY'])/20
    xb=separate_bounds(fx+ix,leaf['width'],sx,tx,dx);yb=separate_bounds(fy+iy,leaf['height'],sy,ty,dy)
    transform={'sx':sx,'sy':sy,'tx':device_translation(sx,tx,dx,xb[0])+round(ix*sx*4)/4,'ty':device_translation(sy,ty,dy,yb[0])+round(iy*sy*4)/4}
    width,height=xb[1]-xb[0],yb[1]-yb[0];local=render_rect(leaf,transform,(width,height))
    if not (0<=xb[0]<xb[1]<=600 and 0<=yb[0]<yb[1]<=400):raise ValueError('Source buffer outside bounded target')
    result=[[0]*4 for _ in range(240000)]
    for y in range(height):
        for x in range(width):result[(yb[0]+y)*600+xb[0]+x]=local[y*width+x]
    return result,{'x_bounds':xb,'y_bounds':yb,'local_transform':transform,'local_size':[width,height]}


def analyze(folder,native,output=None):
    leaf=load_fixture(folder);build,images,matrices,_,_=decode(native)
    assert build['case']==leaf['case'];filters=leaf['case']['placement']['filters']
    assert len(filters)==1 and filters[0]['type']=='BLURFILTER';f=filters[0]
    scores={};metadata=[];pinned=[]
    if output:output.mkdir(parents=True,exist_ok=True)
    for i,props in enumerate(matrices):
        pixels,info=render_cache(leaf,props);metadata.append(info);channels=[]
        for channel in range(4):
            image=[[pixels[y*600+x][channel] for x in range(600)] for y in range(400)]
            result=blur(image,f['blurX'],f['blurY'],f['passes'],'grouped');channels.append([v for row in result for v in row])
        filtered=[list(v) for v in zip(*channels)]
        for kind,actual in [('cache',pixels),('authored',filtered)]:
            scores[f'{i}-{kind}']=comparison(actual,images[f'{i}-{kind}'])
            if output:Image.frombytes('RGBA',(600,400),bytes(v for p in actual for v in p)).save(output/f'{i}-{kind}.png')
        if i==1:
            composed=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in filtered]
            for tick in leaf['case']['samples']:
                path=ROOT/'evidence/importer-loud-fail/r21/components'/Path(leaf['source']).stem/f"{leaf['case']['id']}-{tick:03d}.native.png"
                target=list(Image.open(path).convert('RGBA').getdata())
                pinned.append({'tick':tick,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(composed,target)})
    return {'metadata':metadata,'comparisons':scores,'pinned_comparisons':pinned,'authored_fill_masks':leaf['fill_masks'],
            'source_derived_cpu_component_exact':all(v['exact']==v['samples'] for v in list(scores.values())+pinned),'gpu_binding_verified':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.fixture,a.native,a.output);(a.output/'analysis.json').write_text(json.dumps(r,separators=(',',':'))+'\n')
    for name,v in r['comparisons'].items():print(name,v['exact'],v['samples'],v['max_channel_delta'])
    print('pinned',[(v['exact'],v['samples']) for v in r['pinned_comparisons']])
