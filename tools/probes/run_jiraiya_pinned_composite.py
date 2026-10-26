"""Require the bounded source-derived diagnostic to match the original54-suite RGB images."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image
from tools.probes.run_jiraiya_source_cache_gpu import run as render_source
from tools.probes.analyze_jiraiya_filter_boundary import ROOT,comparison


def compare(output):
    results=[]
    for i,tick in enumerate((0,3)):
        name=f'jiraiya-342-766-27-{tick:03d}.native.png'
        reference=ROOT/'evidence/importer-loud-fail/r21/components/jiraiya'/name
        actual=Image.open(output/f'final-{i}.png').convert('RGBA')
        native=Image.open(reference).convert('RGBA')
        assert actual.size==native.size==(600,400)
        results.append({'tick':tick,'reference':str(reference.relative_to(ROOT)),'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),**comparison(list(actual.getdata()),list(native.getdata()))})
    return {'images':results,'exact_images':sum(v['exact']==v['samples'] for v in results),'production_admitted':False,'full_production_suite_rerun':False}


def run(godot,output):
    output.mkdir(parents=True,exist_ok=True)
    source=output/'source';render_source(godot,source)
    cases=json.loads((ROOT/'evidence/importer-loud-fail/r21/components/jiraiya/cases.json').read_text())
    case=next(c for c in cases if c['id']=='jiraiya-342-766-27')
    assert case['frame_count']==case['source_frame_count']==1 and case['samples']==[0,3]
    assert hashlib.sha256((ROOT/case['source']['path']).read_bytes()).hexdigest()==case['source']['sha256']
    metadata=json.loads((source/'report.json').read_text())['metadata'][1]
    fixture={'production_admitted':False,'cases':[{**metadata,'cache_png':str(source/'case-1.png'),'native_tick':tick} for tick in case['samples']]}
    path=output/'fixture.json';path.write_text(json.dumps(fixture,indent=2)+'\n')
    for p in output.glob('*.png'):p.unlink()
    command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s','res://tests/source_cache_composite.gd','--',str(path),str(output)]
    process=subprocess.run(command,capture_output=True,text=True,timeout=300)
    log=process.stdout+process.stderr;(output/'godot.log').write_text(log)
    if process.returncode or 'ERROR' in log or 'SOURCE_CACHE_FILTER_OK production_admitted=false' not in log:raise ValueError('Incomplete composition diagnostic')
    result=compare(output);(output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/run_jiraiya_pinned_composite.py','godot/tests/source_cache_composite.gd','godot/tests/source_cache_filter.gd','godot/tests/nested_integer_composite.gdshader','godot/tests/normal_composition.gdshaderinc']
    provenance={'command':command,'exit':process.returncode,'source_sha256':{s:sha(ROOT/s) for s in files},'godot_sha256':sha(godot),'readback_sha256':{p.name:sha(p) for p in output.glob('*.png')},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.godot.resolve(),a.output.resolve());print('pinned images',r['exact_images'],2)
    raise SystemExit(0 if r['exact_images']==2 else 1)
