"""Bind source nearest geometry to uncached wrapper boundaries without faking cache input."""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_matrix_component_boundaries import decode
from tools.probes.analyze_nearest_component_input import decode as leaf_decode
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_rounded_footprint import prepare
from tools.probes.analyze_affine_scan_translation import vertices, fixed_scan
from tools.probes.build_bound_bitmap_component import ROOT


def analyze():
    graph_path=ROOT/'evidence/importer-loud-fail/r156/main-fixture.json.gz'
    graph=json.loads(gzip.decompress(graph_path.read_bytes()))
    fixture,_,leaf_cases=leaf_decode(ROOT/'evidence/importer-loud-fail/r179/native')
    build,images,matrices,clocks,props,restores=decode(ROOT/'evidence/importer-loud-fail/r157/main')
    assert graph['case']==build['case']
    source=ROOT/build['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==build['source_sha256']
    placement=graph['case']['placement'];cx=placement['color_transform']
    assert [cx[c+'MultTerm'] for c in ('red','green','blue','alpha')]==[0,0,0,256]
    assert [cx[c+'AddTerm'] for c in ('red','green','blue','alpha')]==[57,148,230,0]
    key=leaf_cases[1]['key'][3:15];fixed=prepare(tuple(inverse_signed(['0']*5+key)),'ties_even')
    counts=fixed_scan(vertices(['0']*3+['137','200']+key),0,0,600,400,16,'trunc')
    samples=[]
    for i,n in enumerate(counts):
        if not n:samples.append(None);continue
        x,y=i%600,i//600
        ix,iy=((a*x+b*y+t+offset)//65536 for a,b,t,offset,_ in fixed)
        samples.append(max(0,min(199,iy))*137+max(0,min(136,ix)))
    rows=[]
    for tick in build['case']['samples']:
        frame=next(v['frame'] for v in clocks if v['tick']==tick and v['path']==build['case']['id']+'/1')
        slot=graph['frames'][frame-1];shape=slot['shape_id'];source_pixels=None
        if shape is not None:
            leaf=graph['leaves'][str(shape)]
            assert leaf['smooth_sampling'] is False and leaf['fill']['fillStyleType']=='67'
            assert leaf['fill_masks']==fixture['leaf']['fill_masks']
            assert all(p[3] in (0,255) for p in leaf['pixels_premultiplied'])
            source_pixels=leaf['pixels_premultiplied']
        else:
            assert frame==17 and slot['playing_after_actions'] is False
        comparisons={}
        for method in ('tint_before_coverage','tint_after_alpha255','tint_after_alpha256'):
            expected=[]
            for i,n in enumerate(counts):
                pixel=[0]*4
                if n and source_pixels is not None and source_pixels[samples[i]][3]:
                    alpha=255*n//16
                    if method=='tint_before_coverage':pixel=[v*n//16 for v in (57,148,230,255)]
                    elif method=='tint_after_alpha255':pixel=[v*alpha//255 for v in (57,148,230)]+[alpha]
                    else:pixel=[v*(alpha+1)//256 for v in (57,148,230)]+[alpha]
                expected.append(pixel)
            for boundary in ('clear','cache','authored'):
                target=images[f'{tick}-{boundary}'];failures=[];maximum=0
                for i,(actual,native) in enumerate(zip(expected,target)):
                    maximum=max(maximum,max(abs(a-b) for a,b in zip(actual,native)))
                    if actual!=native:failures.append({'x':i%600,'y':i//600,'actual':actual,'native':native})
                comparisons[method+'/'+boundary]={'samples':240000,'exact':240000-len(failures),'max_channel_delta':maximum,'failures':failures}
        rows.append({'tick':tick,'frame':frame,'shape_id':shape,'comparisons':comparisons})
    return {'rows':rows,'clocks_exact':len(clocks),'restores':restores,
            'authored_color_transform':cx,'filter_properties':props,'matrix_readbacks':matrices,
            'cache_boundary_admitted':False,'complete_wrapper_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze();a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for row in r['rows']:
        print(row['tick'],{k:(v['exact'],v['max_channel_delta']) for k,v in row['comparisons'].items()})
