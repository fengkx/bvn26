"""Rebase fixed sampling before quantization; retain every native cache boundary gate."""
import argparse
from fractions import Fraction
import gzip
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_indexed_nearest_cache import decode,comparison
from tools.probes.analyze_matrix_component_boundaries import decode as wrapper_decode
from tools.probes.analyze_nearest_component_input import decode as leaf_decode
from tools.probes.analyze_affine_cache_coordinates import local_translation
from tools.probes.analyze_affine_cache_support import bounds
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_rounded_footprint import prepare
from tools.probes.analyze_affine_scan_translation import fixed_scan,vertices
from tools.probes.build_bound_bitmap_component import ROOT


def layout(properties,method):
    key=['0']*3+['137','200']+properties;origin=bounds(key,'separate')[:2]
    translation=local_translation(key,origin,method)
    key[9:11]=list(map(str,translation));key[15:17]=['0','0']
    fixed=prepare(tuple(inverse_signed(key)),'ties_even')
    counts=fixed_scan(vertices(key),-origin[0],-origin[1],600,400,16,'trunc')
    indices=[]
    for i,count in enumerate(counts):
        if not count:indices.append(None);continue
        x,y=i%600-origin[0],i//600-origin[1]
        ix,iy=((a*x+b*y+t+offset)//65536 for a,b,t,offset,_ in fixed)
        indices.append(max(0,min(199,iy))*137+max(0,min(136,ix)))
    return {'origin':origin,'translation':list(map(str,translation)),'counts':counts,'indices':indices}


def render(source,spec):
    return [[v*count//16 for v in source[index]] if count and source is not None else [0]*4
            for count,index in zip(spec['counts'],spec['indices'])]


def synthetic(root):
    rows=[]
    for axis in ('x','y'):
        for alpha in ('opaque','original'):
            name=axis+'-'+alpha;fixture,source,cases=decode(root/name)
            for method in ('baseline','rounded_sum'):
                spec=layout(cases[0]['key'][3:15],method);actual=render(source,spec)
                rows.append({'input':name,'method':method,'origin':spec['origin'],'translation':spec['translation'],
                             'indexed':comparison(actual,cases[1]['pixels']),'materialized':comparison(actual,cases[3]['pixels'])})
    return rows


def original():
    graph=json.loads(gzip.decompress((ROOT/'evidence/importer-loud-fail/r156/main-fixture.json.gz').read_bytes()))
    fixture,_,leaf_cases=leaf_decode(ROOT/'evidence/importer-loud-fail/r179/native')
    build,images,matrices,clocks,props,restores=wrapper_decode(ROOT/'evidence/importer-loud-fail/r157/main')
    assert graph['case']==build['case']
    placement=build['case']['placement'];cx=placement['color_transform']
    assert [cx[c+'MultTerm'] for c in ('red','green','blue','alpha')]==[0,0,0,256]
    assert [cx[c+'AddTerm'] for c in ('red','green','blue','alpha')]==[57,148,230,0]
    matrix=placement['filters'][0]['matrix'];assert len(matrix)==20 and matrix[15:]==[0,0,0,1,0]
    spec=layout(leaf_cases[1]['key'][3:15],'baseline')
    alternative=layout(leaf_cases[1]['key'][3:15],'rounded_sum')
    assert spec==alternative
    rows=[]
    for tick in build['case']['samples']:
        frame=next(v['frame'] for v in clocks if v['tick']==tick and v['path']==build['case']['id']+'/1')
        slot=graph['frames'][frame-1];shape=slot['shape_id'];source=None
        if shape is not None:
            leaf=graph['leaves'][str(shape)];assert leaf['fill_masks']==fixture['leaf']['fill_masks']
            assert leaf['fill']['fillStyleType']=='67' and leaf['smooth_sampling'] is False
            source=leaf['pixels_premultiplied'];assert all(p[3] in (0,255) for p in source)
        else:assert frame==17 and slot['playing_after_actions'] is False
        raw=render(source,spec)
        cache=[[v*(p[3]+1)//256 for v in (57,148,230)]+[p[3]] if p[3] else [0]*4 for p in raw]
        # This bounded final-output proof consumes the authored dependency:
        # the matrix alpha row is identity, and the following RGB multipliers are zero.
        # It does not prove the discarded intermediate matrix RGB buffer.
        authored=[[v*p[3]//255 for v in (57,148,230)]+[p[3]] for p in raw]
        stage=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in authored]
        path=ROOT/f'evidence/importer-loud-fail/r21/components/main/{build["case"]["id"]}-{tick:03d}.native.png'
        pinned=[list(p) for p in Image.open(path).convert('RGBA').getdata()]
        comparisons={name:comparison(actual,images[f'{tick}-{name}']) for name,actual in [('cache',cache),('authored',authored),('stage',stage)]}
        comparisons['pinned_stage']=comparison(stage,pinned)
        rows.append({'tick':tick,'frame':frame,'shape_id':shape,'comparisons':comparisons})
    return {'rows':rows,'origin':spec['origin'],'translation':spec['translation'],'clocks_exact':len(clocks),
            'matrix_properties':props,'authored_color_transform':cx,'matrix_alpha_row':matrix[15:],
            'matrix_rgb_intermediate_proved':False,'cpu_final_wrapper_exact':all(v['comparisons']['pinned_stage']['exact']==240000 for v in rows)}


def analyze(root):
    return {'synthetic':synthetic(root),'original':original(),'general_cache_initializer_admitted':False,
            'production_admitted':False,'full_production_suite_rerun':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for row in r['synthetic']:print(row['input'],row['method'],row['indexed']['exact'],row['materialized']['exact'])
    for row in r['original']['rows']:print('original',row['tick'],{k:v['exact'] for k,v in row['comparisons'].items()})
