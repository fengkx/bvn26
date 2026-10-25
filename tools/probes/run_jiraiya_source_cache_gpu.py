"""GPU source-derived cache, actual diagnostic filter buffers, and exact native image gates."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image
from tools.probes.analyze_jiraiya_source_cache import ROOT,render_cache
from tools.probes.analyze_jiraiya_bitmap_binding import decode as leaf_reference
from tools.probes.analyze_jiraiya_cache_boundary import decode as native_reference
from tools.probes.analyze_jiraiya_filter_boundary import comparison


def compare_readbacks(output,metadata,native):
    scores={}
    for i,m in enumerate(metadata):
        left,top=m['x_bounds'][0],m['y_bounds'][0]
        for stage in ('cache','input','filtered','final'):
            filename=f'case-{i}.png' if stage=='cache' else f'{stage}-{i}.png'
            image=Image.open(output/filename).convert('RGBA')
            expected_size=(75,74) if stage=='cache' else ((600,400) if stage=='final' else (117,74))
            assert image.size==expected_size
            if stage=='final':target=native[f'{i}-authored']
            else:
                source=native[f'{i}-cache' if stage in ('cache','input') else f'{i}-authored']
                origin=left if stage=='cache' else left-21
                target=[source[(top+y)*600+origin+x] for y in range(image.height) for x in range(image.width)]
            scores[f'{i}-{stage}']=comparison(list(image.getdata()),target)
    return scores


def run(godot,output):
    output.mkdir(parents=True,exist_ok=True)
    leaf,_=leaf_reference(ROOT/'evidence/importer-loud-fail/r89/native')
    props=json.loads(gzip.decompress((ROOT/'evidence/importer-loud-fail/r99/analysis.json.gz').read_bytes()))['properties']
    native,_,_=native_reference(ROOT/'evidence/importer-loud-fail/r100/native')
    metadata=[render_cache(leaf,props[i])[1] for i in (0,3,6)]
    assert all(m['local_size']==[75,74] for m in metadata)
    fixture={**leaf,'target_size':[75,74],'cases':[m['local_transform'] for m in metadata],'production_admitted':False}
    path=output/'leaf.json';path.write_text(json.dumps(fixture,separators=(',',':'))+'\n')
    commands=[]
    def invoke(script,fixture,marker):
        command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s','res://tests/'+script,'--',str(fixture),str(output)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=300)
        log=result.stdout+result.stderr;(output/(script+'.log')).write_text(log)
        commands.append({'command':command,'exit':result.returncode})
        if result.returncode or 'ERROR' in log or marker not in log:raise ValueError('Incomplete GPU diagnostic: '+script)
    for pattern in ('case-*.png','input-*.png','filtered-*.png','final-*.png'):
        for p in output.glob(pattern):p.unlink()
    invoke('half_even_bitmap_leaf.gd',path,'HALF_EVEN_BOUND_BITMAP_RENDER_OK cases=3')
    filter_path=output/'filter.json'
    filter_path.write_text(json.dumps({'production_admitted':False,'cases':[{**m,'cache_png':str(output/f'case-{i}.png')} for i,m in enumerate(metadata)]})+'\n')
    invoke('source_cache_filter.gd',filter_path,'SOURCE_CACHE_FILTER_OK production_admitted=false')
    scores=compare_readbacks(output,metadata,native)
    result={'metadata':metadata,'comparisons':scores,'diagnostic_passed':all(v['exact']==v['samples'] for v in scores.values()),'production_admitted':False}
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    sources=['tools/probes/run_jiraiya_source_cache_gpu.py','tools/probes/analyze_jiraiya_source_cache.py','tools/probes/analyze_bitmap_cache_support_grid.py','tools/probes/analyze_cache_device_origin.py','godot/tests/half_even_bitmap_leaf.gd','godot/tests/half_even_bitmap_sampler.gd','godot/tests/half_even_bitmap_sampler.gdshader','godot/tests/source_cache_filter.gd','godot/tests/grouped_blur_filter_group.gd','godot/tests/consumed_extent_filter_group.gd','godot/tests/integer_blur.gdshader','godot/tests/raw_byte_texture.gdshader','godot/filter_group.gd','godot/blend_group.gd']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    provenance={'commands':commands,'source_sha256':{s:sha(ROOT/s) for s in sources},'godot_sha256':sha(godot),'readback_sha256':{p.name:sha(p) for pattern in ('*.png','leaf.json','filter.json','allocations.json') for p in output.glob(pattern)},'native_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'evidence/importer-loud-fail/r100/native/native.log.gz',ROOT/'evidence/importer-loud-fail/r89/native/native.log.gz')},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.godot.resolve(),a.output.resolve())
    for name,v in r['comparisons'].items():print(name,v['exact'],v['samples'],v['max_channel_delta'])
    raise SystemExit(0 if r['diagnostic_passed'] else 1)
