"""Run full authored ColorMatrix and post-CXFORM on a live source-derived nearest cache."""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from PIL import Image
from tools.probes.analyze_matrix_component_boundaries import decode
from tools.probes.analyze_nearest_component_input import decode as leaf_decode
from tools.probes.analyze_affine_cache_coordinates import local_translation
from tools.probes.analyze_affine_cache_support import bounds
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_rounded_footprint import prepare
from tools.probes.analyze_affine_scan_translation import vertices,fixed_scan
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.inventory_bitmap_roundtrip import decode_lossless
from tools.probes.run_native_nested_filters import fixture as cxform_fixture


def fixture(output):
    output.mkdir(parents=True,exist_ok=True)
    graph=json.loads(gzip.decompress((ROOT/'evidence/importer-loud-fail/r156/main-fixture.json.gz').read_bytes()))
    original,_,leaf_cases=leaf_decode(ROOT/'evidence/importer-loud-fail/r179/native')
    build,images,_,clocks,_,_=decode(ROOT/'evidence/importer-loud-fail/r157/main');case=build['case'];assert graph['case']==case
    source=ROOT/case['source']['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==case['source']['sha256']
    tags={str(struct.unpack_from('<H',p)[0]):(p,r) for code,p,r in source_tags(source) if code in (2,36,39)}
    for cid,digest in graph['raw_tag_sha256'].items():assert hashlib.sha256(tags[cid][1]).hexdigest()==digest
    cx=case['placement']['color_transform'];assert [cx[c+'MultTerm'] for c in ('red','green','blue','alpha')]==[0,0,0,256]
    assert [cx[c+'AddTerm'] for c in ('red','green','blue','alpha')]==[57,148,230,0]
    key=['0']*3+['137','200']+leaf_cases[1]['key'][3:15];allocation=bounds(key,'separate');origin=allocation[:2];width,height=allocation[2:]
    translation=local_translation(key,origin,'baseline');key[9:11]=list(map(str,translation));key[15:17]=['0','0']
    fixed=prepare(tuple(inverse_signed(key)),'ties_even');counts=fixed_scan(vertices(key),0,0,width,height,16,'trunc')
    packed=bytearray(width*height*32);coordinates=bytearray(width*height*16)
    for i,count in enumerate(counts):
        if not count:continue
        x,y=i%width,i//width
        for axis,(a,b,t,offset,_) in enumerate(fixed):
            stages=[a*x,b*y,a*x+b*y,a*x+b*y+t,a*x+b*y+t+offset]
            assert all(-2**31+65536<v<2**31-65536 for v in stages)
            for slot,value in enumerate((a,b,t,offset)):struct.pack_into('<i',packed,i*32+(axis*4+slot)*4,value)
        struct.pack_into('<4f',coordinates,i*16,x,y,0,count)
    specs=[]
    for tick in case['samples']:
        frame=next(v['frame'] for v in clocks if v['tick']==tick and v['path']==case['id']+'/1')
        state=graph['frames'][frame-1];shape=state['shape_id'];folder=output/f'tick{tick}';folder.mkdir(exist_ok=True)
        spec={'folder':folder.name,'tick':tick,'frame':frame,'shape_id':shape,'active':shape is not None,'origin':origin,'size':[width,height],
              'filters':case['placement']['filters'],'post_mul':[0,0,0],'post_add':[57,148,230]}
        if shape is not None:
            leaf=graph['leaves'][str(shape)];payload=tags[str(leaf['bitmap_id'])][0]
            cid,w,h,pixels=decode_lossless(payload);assert payload[2]==3 and [w,h]==[137,200] and pixels==leaf['pixels_premultiplied']
            assert leaf['fill_masks']==original['leaf']['fill_masks'] and leaf['fill']['fillStyleType']=='67' and leaf['smooth_sampling'] is False
            (folder/'source.rgba').write_bytes(bytes(c for p in pixels for c in p));(folder/'coefficients.bin').write_bytes(packed);(folder/'coordinates.bin').write_bytes(coordinates)
            spec['source_metadata']={k:v for k,v in leaf.items() if k!='pixels_premultiplied'}
            Image.frombytes('L',(width,height),bytes(counts)).save(folder/'coverage.png')
        else:assert frame==17 and state['playing_after_actions'] is False
        specs.append(spec)
    data={'case':case,'cases':specs,'raw_tag_sha256':graph['raw_tag_sha256'],'source_matrix_bytes':original['source_matrix_bytes'],
          'native_reciprocals':cxform_fixture()['native_reciprocals'],'production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(data,indent=2)+'\n');return data


def compare(output):
    spec=json.loads((output/'fixture.json').read_text());_,images,_,_,_,_=decode(ROOT/'evidence/importer-loud-fail/r157/main')
    rows=[];boundaries=[]
    for case in spec['cases']:
        folder=output/case['folder'];tick=case['tick'];path=ROOT/f'evidence/importer-loud-fail/r21/components/main/{spec["case"]["id"]}-{tick:03d}.native.png'
        actual=Image.open(folder/'final.png').convert('RGBA');native=Image.open(path).convert('RGBA');assert actual.size==native.size==(600,400)
        failures=[];maximum=0
        for i,(p,q) in enumerate(zip(actual.getdata(),native.getdata())):
            maximum=max(maximum,max(abs(a-b) for a,b in zip(p,q)))
            if p!=q:failures.append({'x':i%600,'y':i//600,'actual':list(p),'native':list(q)})
        rows.append({'tick':tick,'samples':240000,'exact':240000-len(failures),'max_channel_delta':maximum,'failures':failures,'native_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        if not case['active']:continue
        x,y=case['origin'];w,h=case['size']
        for name,target_name in [('local','cache'),('input','cache'),('filtered','authored')]:
            image=Image.open(folder/(name+'.png')).convert('RGBA');assert image.size==(w,h)
            target=images[f'{tick}-{target_name}'];fail=[]
            for i,pixel in enumerate(image.getdata()):
                expected=target[(y+i//w)*600+x+i%w][3]
                if pixel[3]!=expected:fail.append({'x':i%w,'y':i//w,'actual_alpha':pixel[3],'native_alpha':expected})
            boundaries.append({'tick':tick,'boundary':name,'samples':w*h,'exact_alpha':w*h-len(fail),'failures':fail})
    return {'images':rows,'alpha_boundaries':boundaries,'exact_images':sum(v['exact']==v['samples'] for v in rows),
            'live_final_wrapper_exact':all(not v['failures'] for v in rows+boundaries),
            'matrix_rgb_intermediate_proved':False,'production_admitted':False,'full_production_suite_rerun':False}


def run(godot,output):
    data=fixture(output)
    for case in data['cases']:
        for name in ['local','input','filtered','final']:(output/case['folder']/(name+'.png')).unlink(missing_ok=True)
    command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s',str(ROOT/'godot/tests/nearest_matrix_component_live.gd'),'--',str(output/'fixture.json'),str(output)]
    p=subprocess.run(command,capture_output=True,text=True,timeout=300);log=p.stdout+p.stderr;(output/'godot.log').write_text(log)
    if p.returncode or 'ERROR' in log or 'NEAREST_MATRIX_COMPONENT_LIVE_OK cases=4' not in log:raise ValueError('Incomplete live matrix diagnostic: '+log)
    result=compare(output);(output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/run_nearest_matrix_component.py','godot/tests/nearest_matrix_component_live.gd','godot/tests/affine_component_coverage.gdshader','godot/filter_group.gd','godot/blend_group.gd','godot/flash_filter.gdshader','godot/tests/native_nested_filter_composite.gdshader','godot/tests/native_cxform.gdshaderinc','godot/tests/normal_composition.gdshaderinc','tools/probes/analyze_affine_scan_translation.py','evidence/importer-loud-fail/r156/main-fixture.json.gz','evidence/importer-loud-fail/r157/main/native.log.gz']
    provenance={'command':command,'exit':p.returncode,'godot_sha256':sha(godot),'source_sha256':{n:sha(ROOT/n) for n in files},
                'readback_sha256':{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file() and p.name!='provenance.json'},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=run(a.godot.resolve(),a.output.resolve());print('exact',r['exact_images'],'/4',r['live_final_wrapper_exact']);raise SystemExit(0 if r['live_final_wrapper_exact'] else 1)
