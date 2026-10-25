"""Isolated GPU half-step candidate with unchanged native and source-bound gates."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PIL import Image
from tools.probes.build_bitmap_godot_fixture import build
from tools.probes.run_bitmap_godot_fixture import validate_report
from tools.probes.analyze_jiraiya_bitmap_binding import decode,ROOT


def compare_leaves(source,expected,output):
    leaves=[]
    for i,target in enumerate(expected):
        image=Image.open(output/f'case-{i}.png').convert('RGBA');assert image.size==tuple(source['target_size'])
        failures=[{'x':j%image.width,'y':j//image.width,'actual':list(p),'native':q} for j,(p,q) in enumerate(zip(image.getdata(),target)) if list(p)!=q]
        leaves.append({'case':i,'samples':len(target),'exact':len(target)-len(failures),'failures':failures})
    return leaves


def run(godot,output):
    output.mkdir(parents=True,exist_ok=True)
    project=output/'project';scripts=project/'tests';scripts.mkdir(parents=True,exist_ok=True)
    (project/'project.godot').write_text('[application]\nconfig/name="Half-even isolated diagnostic"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\ntextures/default_filters/use_nearest_mipmap_filter=false\n')
    paths=['godot/tests/half_even_bitmap_sampler.gd','godot/tests/half_even_bitmap_sampler.gdshader','godot/tests/half_even_bitmap_leaf.gd','godot/tests/bitmap_sampler_diagnostic.gdshader']
    for path in paths:shutil.copy(ROOT/path,scripts/Path(path).name)
    # Reuse the complete pinned renderer, changing only its diagnostic coordinate provider.
    original=(ROOT/'godot/tests/bitmap_sampler_native_render.gd').read_text()
    before='preload("res://tests/bitmap_sampler_diagnostic.gd")'
    assert original.count(before)==1
    (scripts/'controls.gd').write_text(original.replace(before,'preload("res://tests/half_even_bitmap_sampler.gd")'))
    fixture=build();fp=output/'controls.json';fp.write_text(json.dumps(fixture,separators=(',',':'))+'\n')
    source,expected=decode(ROOT/'evidence/importer-loud-fail/r89/native')
    lp=output/'leaf.json';lp.write_text(json.dumps(source,separators=(',',':'))+'\n')
    commands=[]
    for name,script,args,marker in [('controls','controls.gd',[fp,output/'gpu.json'],'BITMAP_NATIVE_GPU_REFERENCE_OK'),('leaf','half_even_bitmap_leaf.gd',[lp,output],'HALF_EVEN_BOUND_BITMAP_RENDER_OK')]:
        command=[str(godot),'--path',str(project),'--rendering-method','gl_compatibility','--quit-after','600','-s','res://tests/'+script,'--',*[str(p) for p in args]]
        result=subprocess.run(command,capture_output=True,text=True,timeout=300);log=result.stdout+result.stderr;(output/(name+'.log')).write_text(log)
        commands.append({'command':command,'exit':result.returncode})
        if result.returncode or 'ERROR' in log or marker not in log:raise ValueError('GPU diagnostic did not complete: '+name)
    gpu=json.loads((output/'gpu.json').read_text());validate_report(gpu,fixture,hashlib.sha256(fp.read_bytes()).hexdigest())
    leaves=compare_leaves(source,expected,output)
    report={'controls':gpu,'leaves':leaves,'exact_images':sum(not c['failures'] for c in leaves),'production_admitted':False}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    paths+=['godot/tests/bitmap_sampler_native_render.gd','tools/probes/run_half_even_bitmap.py']
    provenance={'commands':commands,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'godot_sha256':hashlib.sha256(godot.read_bytes()).hexdigest(),'reference_sha256':fixture['reference_sha256'],'source_leaf_reference_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'evidence/importer-loud-fail/r89/native').iterdir() if p.is_file()},'readback_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.png')},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    if report['exact_images']!=6:raise ValueError('Source-bound leaf mismatch')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();r=run(args.godot.resolve(),args.output.resolve());print('controls',r['controls']['exact'],'images',r['exact_images'])
