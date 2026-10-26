"""Remeasure original source images with frozen static display composition only."""
import argparse
from fractions import Fraction as Q
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes import run_jinye_wrapper_cpu as original
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.model_flash_float_compose import scene_matrix
from tools.probes.analyze_jinye_affine_initializers import fixed_rows
from tools.probes.analyze_jinye_smooth_leaf import source_geometry,inside

MODEL='r249_static_display_hierarchy/retained_exact_fill/minimum'


def candidate_rows(spec,shape):
    matrix,_=scene_matrix(spec,shape)
    return fixed_rows(matrix,'minimum')


def geometry_sets(leaves,size=(600,400)):
    interior=set();covered=set();width,height=size
    for leaf in leaves:
        polygon=[list(map(Q,point)) for point in leaf['polygon']]
        x0=max(0,math.floor(min(p[0] for p in polygon)));x1=min(width,math.ceil(max(p[0] for p in polygon)))
        y0=max(0,math.floor(min(p[1] for p in polygon)));y1=min(height,math.ceil(max(p[1] for p in polygon)))
        for y in range(y0,y1):
            for x in range(x0,x1):
                if all(inside(point,polygon) for point in ((x,y),(x+1,y),(x+1,y+1),(x,y+1))):interior.add((x,y));covered.add((x,y))
                elif original.coverage(polygon,x,y)>0:covered.add((x,y))
    return interior,covered-interior


def partition(measurement,sets,size=(600,400)):
    interior,edge=sets
    counts={'interior':len(interior),'edge':len(edge),'outside':size[0]*size[1]-len(interior)-len(edge)}
    failures={key:0 for key in counts}
    for item in measurement['failures']:
        xy=item['x'],item['y'];key='interior' if xy in interior else 'edge' if xy in edge else 'outside';failures[key]+=1
    assert sum(counts.values())==measurement['samples'] and sum(failures.values())==measurement['samples']-measurement['exact']
    return {key:{'samples':count,'exact':count-failures[key],'failures':failures[key]} for key,count in counts.items()}


def run(dump,output):
    pin_path=ROOT/'evidence/importer-loud-fail/r249/provenance.json';pins=json.loads(pin_path.read_text())['files']
    for path,digest in pins.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    prior_path=ROOT/'evidence/importer-loud-fail/r249/evaluation.json.gz';prior=json.loads(gzip.decompress(prior_path.read_bytes()))
    assert prior['nearest_scores']['static_hierarchy']['samples']-prior['nearest_scores']['static_hierarchy']['exact']==81
    assert prior['candidate_admitted'] is False
    baseline_path=ROOT/'evidence/importer-loud-fail/r241/wrapper/report.json';baseline=json.loads(baseline_path.read_text())
    default=original.run(dump,output/'default-replay')
    default=json.loads(json.dumps(default))
    assert default['images']==baseline['images'] and default['isolated_leaf_boundaries']==baseline['isolated_leaf_boundaries']
    result=original.run(dump,output/'candidate',row_builder=candidate_rows,model_name=MODEL)
    assert len(result['images'])==len(baseline['images'])==4 and len(result['isolated_leaf_boundaries'])==len(baseline['isolated_leaf_boundaries'])==4
    pairs=[]
    for before,after in zip(baseline['images'],result['images']):
        for key in ('tick','source_frame','active','depths','pinned_image_sha256','candidate_buffer_bounds'):assert before[key]==after[key]
        assert [leaf['polygon'] for leaf in before['leaves']]==[leaf['polygon'] for leaf in after['leaves']]
        sets=geometry_sets(after['leaves']);pairs.append({'tick':after['tick'],'active':after['active'],**{key:{'before':{**before[key],'partitions':partition(before[key],sets)},'after':{**after[key],'partitions':partition(after[key],sets)}} for key in ('uncached','cached','authored','stage')}})
    leaves=[]
    for before,after in zip(baseline['isolated_leaf_boundaries'],result['isolated_leaf_boundaries']):
        for key in ('case','cached','polygon','coverage_model','geometry_samples'):assert before[key]==after[key]
        sets=geometry_sets([after]);leaves.append({'case':after['case'],'cached':after['cached'],'before':{**before,'partitions':partition(before,sets)},'after':{**after,'partitions':partition(after,sets)}})
    summary={'complete_stage_exact_before':baseline['exact_images'],'complete_stage_exact_after':result['exact_images'],'active_stage_exact_before':baseline['exact_active_images'],'active_stage_exact_after':result['exact_active_images'],
             'leaf_exact_before':sum(not row['failures'] for row in baseline['isolated_leaf_boundaries']),'leaf_exact_after':sum(not row['failures'] for row in result['isolated_leaf_boundaries'])}
    report={'partition_semantics':{'complete':'union of leaf interiors; a different overlapping leaf may still contribute edge coverage','leaf':'single authored polygon, full-pixel interior versus intersecting edge versus outside'},'default_replay_matches_r241':True,'summary':summary,'complete_images':pairs,'leaf_images':leaves,'retained_cached_control_failures':81,'changed_only':'display matrix composition provider; source fill precision, inverse footprint, HV sampling, coverage, cache allocation and compositing unchanged',
            'source':result['source'],'decoder':result['decoder'],'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (pin_path,prior_path,baseline_path)},
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False,'component_inventory_advanced':False}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dump',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True);report=run(args.dump,args.output);print(json.dumps(report['summary'],indent=2));raise SystemExit(1)
