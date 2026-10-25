"""Require both source-backed Jiraiya placements to pass one shared live GPU buffer path."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image
from tools.probes.analyze_jiraiya_source_cache import ROOT,render_cache as first_cache
from tools.probes.analyze_jiraiya_bitmap_binding import decode as first_leaf
from tools.probes.analyze_translated_component_cache import source_leaf,render_cache as second_cache
from tools.probes.analyze_component_cache_boundaries import decode as second_native
from tools.probes.analyze_jiraiya_filter_boundary import comparison


def fixtures():
    cases=json.loads((ROOT/'evidence/importer-loud-fail/r21/components/jiraiya/cases.json').read_text())
    first,_=first_leaf(ROOT/'evidence/importer-loud-fail/r89/native')
    props=json.loads(gzip.decompress((ROOT/'evidence/importer-loud-fail/r99/analysis.json.gz').read_bytes()))['properties'][3]
    _,a=first_cache(first,props)
    second=source_leaf();build,_,matrices,_,_=second_native(ROOT/'evidence/importer-loud-fail/r124/native')
    _,b=second_cache(second,matrices[1],build['case']['placement']['matrix'])
    result=[]
    for leaf,metadata,depth in [(first,a,27),(second,b,29)]:
        case=next(c for c in cases if c['placement']['depth']==depth)
        assert case['frame_count']==case['source_frame_count']==1 and case['samples']==[0,3]
        result.append({'depth':depth,'fixture':{**leaf,'target_size':metadata['local_size'],'cases':[metadata['local_transform']]*2,'cache_metadata':[{**metadata,'filters':case['placement']['filters']}]*2,'production_admitted':False}})
    return result


def compare(output):
    results=[]
    for depth in (27,29):
        for index,tick in enumerate((0,3)):
            path=ROOT/f'evidence/importer-loud-fail/r21/components/jiraiya/jiraiya-342-766-{depth}-{tick:03d}.native.png'
            native=Image.open(path).convert('RGBA');actual=Image.open(output/str(depth)/f'final-{index}.png').convert('RGBA')
            assert native.size==actual.size==(600,400)
            results.append({'depth':depth,'tick':tick,'native_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(list(actual.getdata()),list(native.getdata()))})
    return {'images':results,'exact_images':sum(v['exact']==v['samples'] for v in results),'shared_live_gpu_path_verified':True,'production_admitted':False,'full_production_suite_rerun':False}


def run(godot,output):
    output.mkdir(parents=True,exist_ok=True);commands=[]
    original=(ROOT/'godot/tests/half_even_bitmap_leaf.gd').read_text();marker='\t\tview.queue_free()';assert original.count(marker)==1
    script=original.replace('extends SceneTree','extends SceneTree\nconst LIVE = preload("res://tests/live_rect_cache_filter.gd")').replace(marker,'\t\tawait LIVE.render(self, view.get_texture(), fixture.cache_metadata[case_index], args[1], case_index)\n'+marker)
    for item in fixtures():
        folder=output/str(item['depth']);folder.mkdir(exist_ok=True)
        path=folder/'fixture.json';path.write_text(json.dumps(item['fixture'],separators=(',',':'))+'\n')
        generated=folder/'live_leaf.gd';generated.write_text(script)
        for p in folder.glob('*.png'):p.unlink()
        command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s',str(generated),'--',str(path),str(folder)]
        process=subprocess.run(command,capture_output=True,text=True,timeout=300)
        log=process.stdout+process.stderr;(folder/'godot.log').write_text(log);commands.append({'command':command,'exit':process.returncode})
        if process.returncode or 'ERROR' in log or 'HALF_EVEN_BOUND_BITMAP_RENDER_OK cases=2' not in log:raise ValueError('Incomplete shared live GPU diagnostic')
    result=compare(output);(output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/run_jiraiya_pair_live.py','tools/probes/analyze_translated_component_cache.py','tools/probes/analyze_jiraiya_source_cache.py','godot/tests/live_rect_cache_filter.gd','godot/tests/half_even_bitmap_leaf.gd','godot/tests/half_even_bitmap_sampler.gd','godot/tests/half_even_bitmap_sampler.gdshader','godot/tests/grouped_blur_filter_group.gd','godot/tests/integer_blur.gdshader','godot/tests/nested_integer_composite.gdshader','godot/tests/normal_composition.gdshaderinc','godot/filter_group.gd']
    provenance={'commands':commands,'source_sha256':{s:sha(ROOT/s) for s in files},'godot_sha256':sha(godot),'readback_sha256':{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file() and p.name!='provenance.json' and p.suffix in ('.png','.gd','.json')},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.godot.resolve(),a.output.resolve());print('shared live pinned images',r['exact_images'],4)
    raise SystemExit(0 if r['exact_images']==4 else 1)
