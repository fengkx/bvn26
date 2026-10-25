"""Expose matrix RGB with all authored post-transform states on the same live cache."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from PIL import Image
from tools.probes.run_nearest_matrix_component import fixture as base_fixture
from tools.probes.analyze_matrix_component_boundaries import decode
from tools.probes.build_bound_bitmap_component import ROOT


def native_path(root,state):
    return ROOT/'evidence/importer-loud-fail/r157/main' if state==1 else root/f'frame{state}'


def fixture(output,native):
    output.mkdir(parents=True,exist_ok=True);base=base_fixture(output/'base')
    pinned=json.loads((ROOT/'evidence/importer-loud-fail/r32/components/main/cases.json').read_text());specs=[]
    for state in (1,2,3):
        build,_,_,clocks,_,_=decode(native_path(native,state));case=build['case'];original=pinned[state-1]
        assert {k:v for k,v in case.items() if k!='wrapper_symbol'}=={k:v for k,v in original.items() if k!='wrapper_symbol'}
        placement=case['placement'];assert placement['matrix']==base['case']['placement']['matrix'] and placement['filters']==base['case']['placement']['filters']
        cx=placement['color_transform'];multipliers=[int(cx.get(c+'MultTerm',256)) for c in ('red','green','blue','alpha')];offsets=[int(cx.get(c+'AddTerm',0)) for c in ('red','green','blue','alpha')]
        assert multipliers[3]==256 and offsets[3]==0
        for source in base['cases']:
            tick=source['tick'];frame=next(v['frame'] for v in clocks if v['tick']==tick and v['path']==case['id']+'/1');assert frame==source['frame']
            folder=output/f'state{state}-tick{tick}';folder.mkdir(exist_ok=True)
            for path in (output/'base'/source['folder']).iterdir():
                if path.is_file():shutil.copy(path,folder/path.name)
            specs.append({**source,'folder':folder.name,'state':state,'case_id':case['id'],'post_mul':multipliers[:3],'post_add':offsets[:3],
                          'authored_color_transform':cx,'filters':placement['filters']})
    result={**base,'cases':specs,'native_root':str(native.resolve()),'production_admitted':False}
    result.pop('case');(output/'fixture.json').write_text(json.dumps(result,indent=2)+'\n');return result


def measure(actual,native,width):
    assert len(actual)==len(native);failures=[];maximum=0
    for i,(p,q) in enumerate(zip(actual,native)):
        maximum=max(maximum,max(abs(a-b) for a,b in zip(p,q)))
        if list(p)!=list(q):failures.append({'x':i%width,'y':i//width,'actual':list(p),'native':list(q)})
    return {'samples':len(actual),'exact':len(actual)-len(failures),'max_channel_delta':maximum,'failures':failures}


def compare(output,native):
    spec=json.loads((output/'fixture.json').read_text());decoded={state:decode(native_path(native,state)) for state in (1,2,3)}
    identity_images=decoded[3][1];rows=[];boundaries=[]
    for case in spec['cases']:
        folder=output/case['folder'];tick=case['tick'];state=case['state']
        path=ROOT/f'evidence/importer-loud-fail/r21/components/main/{case["case_id"]}-{tick:03d}.native.png'
        actual=Image.open(folder/'final.png').convert('RGBA');pinned=Image.open(path).convert('RGBA');assert actual.size==pinned.size==(600,400)
        rows.append({'state':state,'tick':tick,'native_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**measure(list(actual.getdata()),list(pinned.getdata()),600)})
        assert decoded[state][1][f'{tick}-stage']==[list(p) for p in pinned.getdata()]
        if not case['active']:continue
        x,y=case['origin'];w,h=case['size']
        for name,target_name in [('local','cache'),('input','cache'),('filtered','authored')]:
            actual=Image.open(folder/(name+'.png')).convert('RGBA');assert actual.size==(w,h)
            image=identity_images[f'{tick}-{target_name}'];target=[image[(y+j)*600+x+i] for j in range(h) for i in range(w)]
            boundaries.append({'state':state,'tick':tick,'boundary':name,**measure(list(actual.getdata()),target,w)})
    return {'images':rows,'rgba_boundaries':boundaries,'exact_images':sum(v['exact']==v['samples'] for v in rows),
            'full_family_exact':all(not v['failures'] for v in rows+boundaries),'production_admitted':False,'full_production_suite_rerun':False}


def run(godot,native,output):
    spec=fixture(output,native)
    for case in spec['cases']:
        for name in ['local','input','filtered','final']:(output/case['folder']/(name+'.png')).unlink(missing_ok=True)
    command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','1200','-s',str(ROOT/'godot/tests/nearest_matrix_family_live.gd'),'--',str(output/'fixture.json'),str(output)]
    p=subprocess.run(command,capture_output=True,text=True,timeout=300);log=p.stdout+p.stderr;(output/'godot.log').write_text(log)
    if p.returncode or 'ERROR' in log or 'NEAREST_MATRIX_FAMILY_LIVE_OK cases=12' not in log:raise ValueError('Incomplete matrix-family diagnostic: '+log)
    result=compare(output,native);(output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/run_nearest_matrix_family.py','tools/probes/run_nearest_matrix_component.py','godot/tests/nearest_matrix_family_live.gd','godot/tests/affine_component_coverage.gdshader','godot/filter_group.gd','godot/blend_group.gd','godot/flash_filter.gdshader','godot/tests/native_nested_filter_composite.gdshader','godot/tests/native_cxform.gdshaderinc','godot/tests/normal_composition.gdshaderinc']
    provenance={'command':command,'exit':p.returncode,'godot_sha256':sha(godot),'source_sha256':{n:sha(ROOT/n) for n in files},
                'readback_sha256':{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file() and p.name!='provenance.json'},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=run(a.godot.resolve(),a.native.resolve(),a.output.resolve());print('exact',r['exact_images'],'/12',r['full_family_exact']);raise SystemExit(0 if r['full_family_exact'] else 1)
