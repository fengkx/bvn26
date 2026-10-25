"""Bind original indexed component texels and geometry to live GPU filter buffers."""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.inventory_bitmap_roundtrip import decode_lossless
from tools.probes.analyze_indexed_twip_component import render_cache
from tools.probes.analyze_animated_component_boundaries import decode
from tools.probes.analyze_clipped_half_step import axis
from tools.probes.analyze_jiraiya_filter_boundary import comparison


def fixture():
    source=json.loads((ROOT/'evidence/importer-loud-fail/r142/fixture.json').read_text());case=source['case']
    path=ROOT/case['source']['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==case['source']['sha256']
    tags={str(struct.unpack_from('<H',p)[0]):(p,r) for c,p,r in source_tags(path) if c in (2,36,39)}
    for cid,digest in source['raw_tag_sha256'].items():assert hashlib.sha256(tags[cid][1]).hexdigest()==digest
    build,_,matrices,clocks,_,_=decode(ROOT/'evidence/importer-loud-fail/r141/native');assert case==build['case'];cases=[]
    for tick,matrix in zip(case['samples'],matrices):
        frame=next(v['frame'] for v in clocks if v['tick']==tick and v['path']==case['id']+'/'+str(case['placement']['depth']))
        state=source['frames'][frame-1];leaf={**source['leaves'][str(state['shape_id'])],'inner_matrix':state['inner_matrix']}
        payload=tags[str(leaf['bitmap_id'])][0];assert payload[2]==3
        cid,w,h,raw=decode_lossless(payload);assert [cid,w,h]==[leaf['bitmap_id'],leaf['width'],leaf['height']] and raw==leaf['pixels_premultiplied']
        leaf['indexed_storage_verified']=True
        _,meta=render_cache(leaf,[tick,0]+matrix[1:]);t=meta['local_transform'];fx=float(leaf['fill_matrix']['translateX'])/20;fy=float(leaf['fill_matrix']['translateY'])/20
        left=Fraction(t['tx'])+Fraction(int(leaf['fill_matrix']['translateX']),20);top=Fraction(t['ty'])+Fraction(int(leaf['fill_matrix']['translateY']),20)
        assert all((v*4)%1!=Fraction(1,2) for v in (left,top,left+w,top+h))
        left,right,top,bottom=[round(v*4)/4 for v in (left,left+w,top,top+h)];samples=[]
        for y in range(meta['local_size'][1]):
            for x in range(meta['local_size'][0]):
                u=axis(t['sx'],t['tx'],x,'even')-fx;v=axis(t['sy'],t['ty'],y,'even')-fy;ix,iy=math.floor(u),math.floor(v)
                area=max(0,min(x+1,right)-max(x,left))*max(0,min(y+1,bottom)-max(y,top))
                samples.append([ix,iy,math.floor((u-ix)*256),math.floor((v-iy)*256),area])
        cases.append({**meta,'leaf':leaf,'tick':tick,'native_frame':frame,'samples':samples,'filters':case['placement']['filters']})
    return {'case':case,'source_fixture':source,'cases':cases,'production_admitted':False}


def compare(output):
    data=fixture();_,images,_,_,_,_=decode(ROOT/'evidence/importer-loud-fail/r141/native');rows=[];pinned=[]
    for i,spec in enumerate(data['cases']):
        tick=spec['tick'];xb,yb=spec['x_bounds'],spec['y_bounds'];f=spec['filters'][0]
        px=math.ceil(max(0,(f['blurX']-1)/2))*f['passes'];py=math.ceil(max(0,(f['blurY']-1)/2))*f['passes']
        cache=Image.frombytes('RGBA',(600,400),bytes(c for p in images[f'{tick}-cache'] for c in p));filtered=Image.frombytes('RGBA',(600,400),bytes(c for p in images[f'{tick}-authored'] for c in p))
        for name,target in [('local',cache.crop((xb[0],yb[0],xb[1],yb[1]))),('input',cache.crop((xb[0]-px,yb[0]-py,xb[1]+px,yb[1]+py))),('filtered',filtered.crop((xb[0]-px,yb[0]-py,xb[1]+px,yb[1]+py)))]:
            actual=Image.open(output/f'{name}-{i}.png').convert('RGBA');assert actual.size==target.size
            rows.append({'tick':tick,'boundary':name,**comparison(list(actual.getdata()),list(target.getdata()))})
        path=ROOT/f"evidence/importer-loud-fail/r21/components/lanran/{data['case']['id']}-{tick:03d}.native.png"
        actual=Image.open(output/f'final-{i}.png').convert('RGBA');target=Image.open(path).convert('RGBA');assert actual.size==target.size==(600,400)
        pinned.append({'tick':tick,'native_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**comparison(list(actual.getdata()),list(target.getdata()))})
    return {'boundaries':rows,'pinned':pinned,'exact_images':sum(v['exact']==v['samples'] for v in pinned),'live_indexed_component_exact':all(v['exact']==v['samples'] for v in rows+pinned),'production_admitted':False,'full_production_suite_rerun':False}


def run(godot,output):
    output.mkdir(parents=True,exist_ok=True);path=output/'fixture.json';path.write_text(json.dumps(fixture(),separators=(',',':'))+'\n')
    for p in output.glob('*.png'):p.unlink()
    command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s',str(ROOT/'godot/tests/indexed_component_live.gd'),'--',str(path),str(output)]
    p=subprocess.run(command,capture_output=True,text=True,timeout=300);log=p.stdout+p.stderr;(output/'godot.log').write_text(log)
    if p.returncode or 'ERROR' in log or 'INDEXED_COMPONENT_LIVE_OK cases=4' not in log:raise ValueError('Incomplete indexed GPU diagnostic: '+log)
    result=compare(output);(output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    files=['tools/probes/run_indexed_component_live.py','tools/probes/indexed_twip_rect_candidate.py','godot/tests/indexed_component_live.gd','godot/tests/quarter_grid_bitmap_input.gdshader','godot/tests/live_rect_cache_filter.gd','godot/tests/grouped_blur_filter_group.gd','godot/tests/integer_blur.gdshader','godot/tests/nested_integer_composite.gdshader','godot/tests/normal_composition.gdshaderinc','godot/filter_group.gd']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    provenance={'command':command,'exit':p.returncode,'source_sha256':{s:sha(ROOT/s) for s in files},'godot_sha256':sha(godot),'readback_sha256':{p.name:sha(p) for p in output.iterdir() if p.is_file() and p.name!='provenance.json'},'production_admitted':False};(output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.godot.resolve(),a.output.resolve());print('exact images',r['exact_images'],'boundaries exact',r['live_indexed_component_exact']);raise SystemExit(0 if r['live_indexed_component_exact'] else 1)
