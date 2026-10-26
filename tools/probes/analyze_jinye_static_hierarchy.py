"""Reject a single byte-derived compose sequence on retained source controls."""
import argparse
from fractions import Fraction as Q
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jinye_affine_initializers import fixed_rows
from tools.probes.analyze_jinye_smooth_leaf import source_geometry,inside
from tools.probes.analyze_jinye_inverse_translation_order import consumed_matrix
from tools.probes.analyze_jinye_materialization import decode
from tools.probes.jinye_jpeg_source import decode as decode_source
from tools.probes.run_jinye_wrapper_cpu import coverage
from tools.probes.analyze_jinye_fixed_hv import sample_hv
from tools.probes.run_nearest_matrix_family import measure
from tools.probes.analyze_jinye_nearest_origin import compatible_texel


from tools.probes.model_flash_float_compose import scene_matrix


def analyze(dump,output):
    path=ROOT/'evidence/importer-loud-fail/r233/analysis.json.gz';fixture_path=ROOT/'evidence/importer-loud-fail/r233/native/fixture.json'
    retained=json.loads(gzip.decompress(path.read_bytes()));fixture=json.loads(fixture_path.read_text())
    assert len(retained['cases'])==200
    keys=[(c['case'],c['cached']) for c in retained['cases']]
    assert len(set(keys))==200 and set(keys)=={(spec['id'],cached) for spec in fixture['cases'] for cached in (False,True)}
    scores={name:{'samples':0,'exact':0,'first_failure':None} for name in ('retained','static_hierarchy')};cases=[]
    for case in retained['cases']:
        assert case['samples']==case['texel_compatible']==len(case['codes']) and not case['incompatible']
        spec=fixture['cases'][case['case']];shape=dict(next(s for s in fixture['source_graph']['shapes'] if s['id']==spec['shape']),bitmap_matrix=spec['fill_matrix'])
        candidate,stages=scene_matrix(spec,shape)
        rows={'retained':fixed_rows(consumed_matrix(spec,shape),'minimum'),'static_hierarchy':fixed_rows(candidate,'minimum')}
        assert [list(r) for r in rows['retained']]==case['fixed_coordinate_rows']['scaled_child_then_draw_quarters/minimum']
        assert all(compatible_texel(pixel)==cell for x,y,pixel,cell in case['codes'])
        failures={}
        for name,rr in rows.items():
            failures[name]=[]
            for x,y,pixel,cell in case['codes']:
                got=[max(0,min(limit-1,(a*x+b*y+t+phase)//65536)) for (a,b,t,phase),limit in zip(rr,(92,40))]
                score=scores[name];score['samples']+=1;score['exact']+=got==cell
                if got!=cell:
                    failure={'case':case['case'],'cached':case['cached'],'xy':[x,y],'candidate':got,'native':cell}
                    failures[name].append(failure)
                    if score['first_failure'] is None:score['first_failure']=failure
        cases.append({'case':case['case'],'cached':case['cached'],'stages':stages,'rows':rows,'samples':len(case['codes']),'failures':failures})
    assert scores['retained']['samples']==scores['static_hierarchy']['samples']==436000
    assert scores['retained']['exact']==409816
    native=ROOT/'evidence/importer-loud-fail/r242/native';local_fixture,images,_=decode(native)
    metadata,source=decode_source(dump,output/'decoded');pin=json.loads((ROOT/'evidence/importer-loud-fail/r220/jpeg/analysis/summary.json').read_text());assert metadata['plane_sha256']==pin['bitmap']['plane_sha256'];assert source==images['source']['pixels']
    x,y,w,h=local_fixture['local_allocation'];spec={**local_fixture['cases'][0],'outer':[1,0,0,1,0,0],'draw':[1,0,0,1,-x,-y]};shape=next(s for s in local_fixture['shapes'] if s['id']==56)
    candidate,stages=scene_matrix(spec,shape);_,polygon=source_geometry(spec,shape);local=[]
    for name,matrix in [('retained',consumed_matrix(spec,shape)),('static_hierarchy',candidate)]:
        rr=fixed_rows(matrix,'minimum');pixels=[]
        for yy in range(h):
            for xx in range(w):
                area=coverage(polygon,xx,yy);weight=math.floor(area*256)
                pixels.append([v*weight//256 for v in sample_hv(source,rr,xx,yy)] if weight else [0,0,0,0])
        for cached in (0,1):
            target=images[f'{cached}-local']['pixels'];partitions={key:{'samples':0,'exact':0} for key in ('interior','edge','outside')}
            for index,(actual,expected) in enumerate(zip(pixels,target)):
                xx,yy=index%w,index//w
                key='interior' if all(inside(point,polygon) for point in ((xx,yy),(xx+1,yy),(xx+1,yy+1),(xx,yy+1))) else 'edge' if coverage(polygon,xx,yy)>0 else 'outside'
                partitions[key]['samples']+=1;partitions[key]['exact']+=actual==expected
            measurement=measure(pixels,target,w)
            if name=='retained':assert measurement['exact']==15979 and measurement['samples']==15980
            local.append({'model':name,'cached':bool(cached),'rows':rr,'partitions':partitions,**measurement})
    summary={str(cached):{'samples':sum(c['samples'] for c in cases if c['cached']==cached),'failures':sum(len(c['failures']['static_hierarchy']) for c in cases if c['cached']==cached)} for cached in (False,True)}
    return {'nearest_by_cache':summary,'nearest_scores':scores,'nearest_cases':cases,'local':local,'local_stages':stages,'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (path,fixture_path)},'float_branch_routing_proved':False,'translation_round_mode_proved':False,'fill_routing_proved':False,'inverse_model_changed':False,'old_axis_sampler_suites_advanced':False,'native_component_inventory_advanced':False,'static_model_sha256':hashlib.sha256((ROOT/'tools/probes/model_flash_float_compose.py').read_bytes()).hexdigest(),'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dump',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);r=analyze(a.dump,a.output);(a.output/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'nearest':r['nearest_scores'],'local':[(v['model'],v['exact'],v['samples']) for v in r['local']]},indent=2))
