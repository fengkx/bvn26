"""Bind the complete source Jinye graph to one rejected CPU sampler diagnostic.

Native images are comparison outputs only. Cache bounds and fractional coverage
remain explicit hypotheses; an empty frame cannot admit this complete path.
"""
import argparse
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.inventory_jinye_component import inventory
from tools.probes.jinye_jpeg_source import decode as decode_source
from tools.probes.analyze_cached_component_boundaries import decode as decode_wrapper
from tools.probes.analyze_jinye_leaf_boundaries import decode as decode_leaves
from tools.probes.analyze_jinye_translation_controls import models_for
from tools.probes.analyze_jinye_fixed_hv import sample_hv
from tools.probes.analyze_jinye_smooth_leaf import inside
from tools.probes.normal_composition import over
from tools.probes.run_nearest_matrix_family import measure

MODEL='scaled_child_then_draw_quarters/minimum'
SIZE=(600,400)


def matrix(attributes):
    def fixed(key,default):return Q(round(float(attributes.get(key,default))*65536),65536)
    return [fixed('scaleX',1),fixed('rotateSkew0',0),fixed('rotateSkew1',0),fixed('scaleY',1),Q(int(attributes.get('translateX',0)),20),Q(int(attributes.get('translateY',0)),20)]


def coverage(polygon,x,y):
    """Exact polygon-square area, explicitly unproved as Flash edge coverage."""
    points=list(polygon)
    for axis,edge,sign in ((0,Q(x),1),(0,Q(x+1),-1),(1,Q(y),1),(1,Q(y+1),-1)):
        result=[]
        if not points:return Q(0)
        for a,b in zip(points,points[1:]+points[:1]):
            aa=(a[axis]-edge)*sign>=0;bb=(b[axis]-edge)*sign>=0
            if aa:result.append(a)
            if aa!=bb:
                t=(edge-a[axis])/(b[axis]-a[axis]);result.append(tuple(a[k]+t*(b[k]-a[k]) for k in (0,1)))
        points=result
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1])))/2 if points else Q(0)


def render_leaf(source,spec,shape,size):
    models,_,polygon=models_for(spec,shape);rows=models[MODEL];w,h=size
    pixels=[[0,0,0,0] for _ in range(w*h)];classes={'interior':0,'edge':0};nonzero={'interior':0,'edge':0}
    box=[max(0,math.floor(min(p[0] for p in polygon))),max(0,math.floor(min(p[1] for p in polygon))),min(w,math.ceil(max(p[0] for p in polygon))),min(h,math.ceil(max(p[1] for p in polygon)))]
    for y in range(box[1],box[3]):
        for x in range(box[0],box[2]):
            interior=all(inside(p,polygon) for p in ((x,y),(x+1,y),(x+1,y+1),(x,y+1)))
            area=Q(1) if interior else coverage(polygon,x,y)
            if not area:continue
            kind='interior' if interior else 'edge';classes[kind]+=1
            sampled=sample_hv(source,rows,x,y);weight=math.floor(area*256)
            actual=[value*weight//256 for value in sampled];pixels[y*w+x]=actual;nonzero[kind]+=bool(actual[3])
    return pixels,{'model':MODEL+'/HV','geometry_samples':classes,'nonzero_samples':nonzero,'polygon':[[str(v) for v in p] for p in polygon],'fixed_rows':rows,'coverage_model':'exact_geometric_area_floor256_unproved','sampler_admitted':False,'coverage_admitted':False}


def render_graph(source,placements,shapes,outer,draw,size,origin=(0,0)):
    buffer=[[0,0,0,0] for _ in range(size[0]*size[1])];leaves=[]
    for placement in sorted(placements,key=lambda p:p['depth']):
        shifted=list(draw);shifted[4]-=origin[0];shifted[5]-=origin[1]
        spec={'matrix':matrix(placement['matrix']),'outer':outer,'draw':shifted}
        leaf,metadata=render_leaf(source,spec,shapes[placement['character_id']],size)
        buffer=[over(back,front) if front[3] else back for back,front in zip(buffer,leaf)]
        leaves.append({'depth':placement['depth'],'character_id':placement['character_id'],**metadata})
    return buffer,leaves


def save(path,pixels,size):
    assert len(pixels)==size[0]*size[1] and all(len(p)==4 and all(0<=v<=255 for v in p) for p in pixels)
    image=Image.new('RGBA',size);image.putdata([tuple(p) for p in pixels]);image.save(path)


def gate(report):
    obligations=('complete_wrapper_exact','sampler_admitted','cache_allocation_admitted',
                 'coverage_admitted','ratio_consumption_proved','stream_metadata_semantics_admitted',
                 'local_input_native_exact')
    return all(report.get(key) is True for key in obligations)


def run(dump,output):
    output.mkdir(parents=True,exist_ok=True)
    retained=json.loads((ROOT/'evidence/importer-loud-fail/r220/inventory.json').read_text())
    source_graph=json.loads(json.dumps(inventory(ROOT/'evidence/importer-loud-fail/r220/jinye-bounded.xml')));assert source_graph==retained
    decoder,source=decode_source(dump,output/'decoded')
    pinned_decoder=json.loads((ROOT/'evidence/importer-loud-fail/r220/jpeg/analysis/summary.json').read_text())
    assert decoder['plane_sha256']==pinned_decoder['bitmap']['plane_sha256'] and len(source)==3680
    native,images,readbacks,clocks,_,_=decode_wrapper(ROOT/'evidence/importer-loud-fail/r220/native')
    assert native['case']==source_graph['case']
    shapes={s['id']:s for s in source_graph['shapes']};case=source_graph['case'];normal=case['normalization']
    outer=matrix(case['placement']['matrix']);draw=[Q(normal['scale']),0,0,Q(normal['scale']),Q(normal['x']),Q(normal['y'])]
    rows=[]
    for tick in case['samples']:
        frame=1+tick%21;observed=next(c['frame'] for c in clocks if c['tick']==tick and c['path']==case['id']+'/1');assert frame==observed
        placements=source_graph['graph']['frames'][frame-1]['placements'];folder=output/f'tick{tick}';folder.mkdir(exist_ok=True)
        clear,leaves=render_graph(source,placements,shapes,outer,draw,SIZE)
        if leaves:
            allpoints=[list(map(Q,p)) for leaf in leaves for p in leaf['polygon']]
            x=math.floor(min(p[0] for p in allpoints))-1;y=math.floor(min(p[1] for p in allpoints))-1
            w=math.ceil(max(p[0] for p in allpoints))+1-x;h=math.ceil(max(p[1] for p in allpoints))+1-y
            local,local_leaves=render_graph(source,placements,shapes,outer,draw,(w,h),(x,y));save(folder/'local-cache-candidate.png',local,(w,h))
            cached=[[0,0,0,0] for _ in range(600*400)]
            for yy in range(h):
                for xx in range(w):
                    if 0<=x+xx<600 and 0<=y+yy<400:cached[(y+yy)*600+x+xx]=local[yy*w+xx]
            buffer_bounds=[x,y,w,h]
        else:cached=clear;local_leaves=[];buffer_bounds=None
        stage=[over([96,96,96,255],p) for p in cached]
        save(folder/'clear.png',clear,SIZE);save(folder/'cache-candidate.png',cached,SIZE);save(folder/'stage.png',stage,SIZE)
        target=ROOT/f"evidence/importer-loud-fail/r21/components/jinye/{case['id']}-{tick:03d}.native.png"
        with Image.open(target) as png:assert png.size==SIZE;pinned=[list(p) for p in png.convert('RGBA').getdata()]
        assert pinned==images[f'{tick}-stage']
        rows.append({'tick':tick,'source_frame':frame,'active':bool(placements),'depths':[p['depth'] for p in placements],
                     'leaves':leaves,'local_cache_leaves':local_leaves,'candidate_buffer_bounds':buffer_bounds,
                     'native_property_readback':readbacks[case['samples'].index(tick)],
                     'uncached':measure(clear,images[f'{tick}-clear'],600),'cached':measure(cached,images[f'{tick}-cache'],600),
                     'authored':measure(cached,images[f'{tick}-authored'],600),'stage':measure(stage,pinned,600),
                     'pinned_image_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                     'local_input_boundary_status':'unmeasured_no_independent_native_buffers'})
    leaf_fixture,leaf_native,_=decode_leaves(ROOT/'evidence/importer-loud-fail/r221/native');leaf_rows=[]
    for capture in leaf_native:
        spec=leaf_fixture['cases'][capture['source_case']];pixels,metadata=render_leaf(source,spec,shapes[spec['shape']],SIZE)
        leaf_rows.append({'case':capture['source_case'],'cached':capture['cached'],**metadata,**measure(pixels,capture['pixels'],600)})
    report={'source':source_graph['source'],'decoder':decoder,'source_events':len(source_graph['graph']['events']),
            'model':MODEL+'/HV','images':rows,'isolated_leaf_boundaries':leaf_rows,
            'exact_images':sum(not r['stage']['failures'] for r in rows),'exact_active_images':sum(r['active'] and not r['stage']['failures'] for r in rows),
            'complete_wrapper_exact':all(not r[k]['failures'] for r in rows for k in ('uncached','cached','authored','stage')),
            'sampler_admitted':False,'cache_allocation_admitted':False,'coverage_admitted':False,'ratio_consumption_proved':False,
            'stream_metadata_semantics_admitted':False,'local_input_native_exact':False,
            'production_admitted':False,'component_inventory_advanced':False}
    (output/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dump',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=run(a.dump.resolve(),a.output.resolve());print(json.dumps({k:result[k] for k in ('exact_images','exact_active_images','complete_wrapper_exact','production_admitted')}));raise SystemExit(0 if gate(result) else 1)
