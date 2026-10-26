"""Shared live GPU binding with source-preserved cyclic rectangle masks."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image
from tools.probes.run_jiraiya_pair_live import fixtures as old_fixtures
from tools.probes.analyze_rect_component_cache import load_fixture,render_cache
from tools.probes.analyze_component_cache_boundaries import decode
from tools.probes.analyze_jiraiya_filter_boundary import ROOT,comparison


def fixtures():
    result=[]
    for item in old_fixtures():
        result.append({'id':f"jiraiya-342-766-{item['depth']}",'source':'jiraiya','fixture':item['fixture']})
    leaf=load_fixture(ROOT/'evidence/importer-loud-fail/r129/fixture')
    _,_,matrices,_,_=decode(ROOT/'evidence/importer-loud-fail/r128/native')
    _,metadata=render_cache(leaf,matrices[1])
    case=leaf['case'];assert case['frame_count']==case['source_frame_count']==1 and case['samples']==[0,3]
    result.append({'id':case['id'],'source':Path(leaf['source']).stem,'fixture':{**leaf,'target_size':metadata['local_size'],'cases':[metadata['local_transform']]*2,'cache_metadata':[{**metadata,'filters':case['placement']['filters']}]*2,'production_admitted':False}})
    return result


def compare(output):
    manifest=json.loads((output/'components.json').read_text());results=[]
    assert [(v['id'],v['source']) for v in manifest]==[(v['id'],v['source']) for v in fixtures()]
    for item in manifest:
        for index,tick in enumerate((0,3)):
            path=ROOT/'evidence/importer-loud-fail/r21/components'/item['source']/f"{item['id']}-{tick:03d}.native.png"
            native=Image.open(path).convert('RGBA');actual=Image.open(output/item['id']/f'final-{index}.png').convert('RGBA')
            assert native.size==actual.size==(600,400)
            results.append({'case':item['id'],'tick':tick,'native_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(list(actual.getdata()),list(native.getdata()))})
    return {'images':results,'exact_images':sum(v['exact']==v['samples'] for v in results),'shared_live_gpu_path_verified':True,'authored_masks_preserved':True,'production_admitted':False,'full_production_suite_rerun':False}


def run(godot,output):
    output.mkdir(parents=True,exist_ok=True);commands=[];items=fixtures()
    (output/'components.json').write_text(json.dumps([{k:v for k,v in item.items() if k!='fixture'} for item in items],indent=2)+'\n')
    original=(ROOT/'godot/tests/half_even_bitmap_leaf.gd').read_text();marker='\t\tview.queue_free()';assert original.count(marker)==1
    mask='assert(mask == [[fill_x, fill_y], [fill_x + fixture.width, fill_y], [fill_x + fixture.width, fill_y + fixture.height], [fill_x, fill_y + fixture.height]])'
    assert original.count(mask)==1
    script=original.replace('extends SceneTree','extends SceneTree\nconst LIVE = preload("res://tests/live_rect_cache_filter.gd")\nconst RECT_MASK = preload("res://tests/rect_mask_binding.gd")').replace(mask,'assert(RECT_MASK.matches(mask, fill_x, fill_y, fixture.width, fixture.height))').replace(marker,'\t\tawait LIVE.render(self, view.get_texture(), fixture.cache_metadata[case_index], args[1], case_index)\n'+marker)
    for item in items:
        folder=output/item['id'];folder.mkdir(exist_ok=True)
        path=folder/'fixture.json';path.write_text(json.dumps(item['fixture'],separators=(',',':'))+'\n')
        generated=folder/'live_leaf.gd';generated.write_text(script)
        for p in folder.glob('*.png'):p.unlink()
        command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s',str(generated),'--',str(path),str(folder)]
        process=subprocess.run(command,capture_output=True,text=True,timeout=300)
        log=process.stdout+process.stderr;(folder/'godot.log').write_text(log);commands.append({'command':command,'exit':process.returncode})
        if process.returncode or 'ERROR' in log or 'HALF_EVEN_BOUND_BITMAP_RENDER_OK cases=2' not in log:raise ValueError('Incomplete shared rectangle GPU diagnostic')
    result=compare(output);(output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/run_rect_components_live.py','tools/probes/run_jiraiya_pair_live.py','tools/probes/analyze_rect_component_cache.py','tools/probes/rect_mask_binding.py','godot/tests/rect_mask_binding.gd','godot/tests/live_rect_cache_filter.gd','godot/tests/half_even_bitmap_leaf.gd','godot/tests/half_even_bitmap_sampler.gd','godot/tests/half_even_bitmap_sampler.gdshader','godot/tests/grouped_blur_filter_group.gd','godot/tests/integer_blur.gdshader','godot/tests/nested_integer_composite.gdshader','godot/tests/normal_composition.gdshaderinc','godot/filter_group.gd']
    provenance={'commands':commands,'source_sha256':{s:sha(ROOT/s) for s in files},'godot_sha256':sha(godot),'readback_sha256':{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file() and p.name!='provenance.json' and p.suffix in ('.png','.gd','.json')},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.godot.resolve(),a.output.resolve());print('shared live rectangle images',r['exact_images'],6)
    raise SystemExit(0 if r['exact_images']==6 else 1)
