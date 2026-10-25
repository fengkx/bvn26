"""Connect the unchanged diagnostic sampler directly to live production-created filter nodes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from tools.probes.analyze_jiraiya_source_cache import ROOT,render_cache
from tools.probes.analyze_jiraiya_bitmap_binding import decode
from tools.probes.run_jiraiya_pinned_composite import compare


def run(godot,output):
    output.mkdir(parents=True,exist_ok=True)
    leaf,_=decode(ROOT/'evidence/importer-loud-fail/r89/native')
    props=json.loads(gzip.decompress((ROOT/'evidence/importer-loud-fail/r99/analysis.json.gz').read_bytes()))['properties'][3]
    _,metadata=render_cache(leaf,props)
    fixture={**leaf,'target_size':[75,74],'cases':[metadata['local_transform']]*2,'cache_metadata':[metadata]*2,'production_admitted':False}
    path=output/'fixture.json';path.write_text(json.dumps(fixture,separators=(',',':'))+'\n')
    original=(ROOT/'godot/tests/half_even_bitmap_leaf.gd').read_text()
    marker='\t\tview.queue_free()'
    assert original.count(marker)==1 and original.count('extends SceneTree')==1
    script=original.replace('extends SceneTree','extends SceneTree\nconst LIVE = preload("res://tests/live_source_cache_filter.gd")').replace(marker,'\t\tawait LIVE.render(self, view.get_texture(), fixture.cache_metadata[case_index], args[1], case_index)\n'+marker)
    generated=output/'live_leaf.gd';generated.write_text(script)
    for p in output.glob('*.png'):p.unlink()
    command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s',str(generated),'--',str(path),str(output)]
    process=subprocess.run(command,capture_output=True,text=True,timeout=300)
    log=process.stdout+process.stderr;(output/'godot.log').write_text(log)
    if process.returncode or 'ERROR' in log or 'HALF_EVEN_BOUND_BITMAP_RENDER_OK cases=2' not in log:raise ValueError('Incomplete live GPU diagnostic')
    result=compare(output);result['live_viewport_texture_verified']=True
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/run_jiraiya_live_cache.py','godot/tests/live_source_cache_filter.gd','godot/tests/half_even_bitmap_leaf.gd','godot/tests/half_even_bitmap_sampler.gd','godot/tests/half_even_bitmap_sampler.gdshader','godot/tests/grouped_blur_filter_group.gd','godot/tests/integer_blur.gdshader','godot/tests/nested_integer_composite.gdshader','godot/tests/normal_composition.gdshaderinc','godot/filter_group.gd']
    provenance={'command':command,'exit':process.returncode,'source_sha256':{s:sha(ROOT/s) for s in files},'godot_sha256':sha(godot),'readback_sha256':{p.name:sha(p) for pattern in ('*.png','live_leaf.gd','fixture.json') for p in output.glob(pattern)},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.godot.resolve(),a.output.resolve());print('live pinned images',r['exact_images'],2)
    raise SystemExit(0 if r['exact_images']==2 else 1)
