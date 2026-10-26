"""Require original rotated Yulong input, actual FilterGroup buffers and pinned final images exact."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
from PIL import Image
from tools.probes.analyze_yulong_rotated_source import ROOT,source_leaf,render
from tools.probes.analyze_component_cache_boundaries import decode
from tools.probes.analyze_jiraiya_filter_boundary import comparison


def fixture():
    source,raw=source_leaf();cases=[]
    for shift in (-128,0,128):
        _,metadata=render(source,raw,shift);cases.append({'shift':shift,'origin':metadata['origin']})
    return {'source':source,'raw':raw,'cases':cases,'production_admitted':False}


def compare(output):
    data=fixture();_,images,_,_,_=decode(ROOT/'evidence/importer-loud-fail/r131/native');rows=[];pinned=[]
    for i,spec in enumerate(data['cases']):
        x,y=map(math.floor,spec['origin']);cache=Image.frombytes('RGBA',(600,400),bytes(c for p in images[f'{i}-cache'] for c in p));glow=Image.frombytes('RGBA',(600,400),bytes(c for p in images[f'{i}-authored'] for c in p))
        for name,target in [('local',cache.crop((x,y,x+4,y+35))),('input',cache.crop((x-2,y-2,x+6,y+37))),('glow',glow.crop((x-2,y-2,x+6,y+37)))]:
            actual=Image.open(output/f'{name}-{i}.png').convert('RGBA');assert actual.size==target.size
            rows.append({'case':i,'boundary':name,**comparison(list(actual.getdata()),list(target.getdata()))})
        target=[[r+96*(256-a)//256,g+96*(256-a)//256,b+96*(256-a)//256,255] for r,g,b,a in images[f'{i}-authored']]
        actual=Image.open(output/f'final-{i}.png').convert('RGBA');assert actual.size==(600,400)
        rows.append({'case':i,'boundary':'final-native',**comparison(list(actual.getdata()),target)})
    actual=Image.open(output/'final-1.png').convert('RGBA')
    for tick in data['source']['case']['samples']:
        path=ROOT/f"evidence/importer-loud-fail/r21/components/yulong/{data['source']['case']['id']}-{tick:03d}.native.png"
        pinned.append({'tick':tick,'native_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(list(actual.getdata()),list(Image.open(path).convert('RGBA').getdata()))})
    return {'boundaries':rows,'pinned':pinned,'exact_images':sum(v['exact']==v['samples'] for v in pinned),'live_rotated_glow_diagnostic_exact':all(v['exact']==v['samples'] for v in rows+pinned),'production_admitted':False,'full_production_suite_rerun':False}


def run(godot,output):
    output.mkdir(parents=True,exist_ok=True);path=output/'fixture.json';path.write_text(json.dumps(fixture(),separators=(',',':'))+'\n')
    for p in output.glob('*.png'):p.unlink()
    command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s',str(ROOT/'godot/tests/rotated_glow_component.gd'),'--',str(path),str(output)]
    process=subprocess.run(command,capture_output=True,text=True,timeout=300);log=process.stdout+process.stderr;(output/'godot.log').write_text(log)
    if process.returncode or 'ERROR' in log or 'ROTATED_GLOW_COMPONENT_OK' not in log:raise ValueError('Incomplete rotated live GPU diagnostic: '+log)
    result=compare(output);(output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    files=['tools/probes/run_yulong_rotated_live.py','tools/probes/analyze_yulong_rotated_source.py','godot/tests/rotated_glow_component.gd','godot/tests/quarter_grid_bitmap_input.gdshader','godot/tests/integer_shadow_filter_group.gd','godot/tests/grouped_family_filter_group.gd','godot/tests/integer_blur.gdshader','godot/tests/integer_shadow.gdshader','godot/tests/nested_integer_composite.gdshader','godot/tests/normal_composition.gdshaderinc','godot/filter_group.gd']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    provenance={'command':command,'exit':process.returncode,'source_sha256':{s:sha(ROOT/s) for s in files},'godot_sha256':sha(godot),'readback_sha256':{p.name:sha(p) for p in output.iterdir() if p.is_file() and p.name!='provenance.json'},'production_admitted':False};(output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.godot.resolve(),a.output.resolve());print('pinned images',r['exact_images'],2,'boundaries exact',r['live_rotated_glow_diagnostic_exact']);raise SystemExit(0 if r['live_rotated_glow_diagnostic_exact'] else 1)
