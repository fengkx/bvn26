"""Gate actual-source caller samples on unchanged native pixel boundaries."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_jinye_materialization import decode as baseline_decode
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.build_jinye_profile import WORKLOADS
from tools.probes.run_nested_filters import unpack
from tools.probes.extract_cache_affine_binary import BINARY_SHA256


def append_row(image, values):
    width,height=image['size'];y=int(values[0])
    assert 0<=y<height and len(image['pixels'])==y*width and len(values)==1+2*width
    words=list(map(int,values[1:]));assert all(-(1<<31)<=word<(1<<32) for word in words)
    image['pixels'].extend(unpack(words))
    image['raw'].extend([[(word>>shift)&255 for shift in (16,8,0,24)] for word in words[::2]])


def baseline_label(workload):
    assert workload in WORKLOADS
    return '0-local' if workload=='local_uncached' else '0-direct' if workload=='direct_uncached' else '1-direct'


def verify_built_movie(native, build, built_native=None):
    built_native = native if built_native is None else built_native
    assert json.loads((built_native/'build.json').read_text()) == build
    assert hashlib.sha256((built_native/'game/main.swf').read_bytes()).hexdigest() == build['swf_sha256']


def analyze(native, profile, baseline, built_native=None):
    old_fixture,old_images,old_readbacks=baseline_decode(baseline)
    fixture=json.loads((native/'fixture.json').read_text());build=json.loads((native/'build.json').read_text())
    workload=fixture['profile_workload'];assert workload==build['workload'] and workload in WORKLOADS
    expected={**old_fixture,'profile_workload':workload,'minimum_duration_ms':8000,'draws_per_batch':1000};assert fixture==expected
    assert hashlib.sha256((native/'fixture.json').read_bytes()).hexdigest()==build['fixture_sha256']
    assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    verify_built_movie(native, build, built_native)
    sample=json.loads((profile/'profile.json').read_text());assert sample['capture_complete'] and sample['sample_exit']==0
    assert sample['movie_sha256']==build['swf_sha256'] and not sample['pixel_reference']
    assert sample['binary_sha256']==BINARY_SHA256
    assert ((profile/'sample.txt').read_bytes() if (profile/'sample.txt').exists() else gzip.decompress((profile/'sample.txt.gz').read_bytes())) and (native/'capture-environment.json').exists()
    path=native/'native.log';text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    records=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    target=old_images[baseline_label(workload)];height=target['size'][1]
    expected_kinds=['image']+['row']*40+['matrix','profile','iterations','props','image']+['row']*height+['done']
    assert len(records)==len(expected_kinds)
    images={};active=None;readbacks={}
    for index,(event,kind) in enumerate(zip(records,expected_kinds)):
        assert len(event)==8 and event[1]==build['run_id'] and event[2:6]==[str(index),'0','0','0'] and event[6]==kind
        payload=event[7];values=payload.split(',')
        if kind=='image':
            label='source' if not images else 'final';size=[92,40] if label=='source' else target['size']
            assert values==[label,*map(str,size),'true'];active={'size':size,'pixels':[],'raw':[]};images[label]=active
        elif kind=='row':append_row(active,values)
        elif kind=='matrix':assert list(map(float,values))==old_readbacks['matrix'][0];readbacks['matrix']=list(map(float,values))
        elif kind=='profile':assert payload==workload+';actual-source;caller-sampling-only'
        elif kind=='iterations':
            count,elapsed=map(int,values);assert count>0 and count%1000==0 and elapsed>=8000;readbacks['iterations']=count;readbacks['elapsed_ms']=elapsed
        elif kind=='props':assert values==[workload,'true' if 'cached_' in workload else 'false','0','1'];readbacks['properties']=values
        else:assert payload=='ok'
    assert images['source']==old_images['source'] and images['final']==target
    return {'workload':workload,'source_pixels_exact':3680,'final_pixels_exact':len(target['pixels']),'raw_rgba_exact':True,'premultiplied_rgba_exact':True,
            'baseline_label':baseline_label(workload),'readbacks':readbacks,'profile':sample,'cache_toggle_requested_each_draw':workload=='direct_cached_regenerate',
            'cache_regeneration_proved':False,'operand_route_proved':False,'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);parser.add_argument('--baseline',type=Path,default=ROOT/'evidence/importer-loud-fail/r242/native');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--built-native-root',type=Path,help='Explicit retained native build root; each original build receipt and movie hash must match');args=parser.parse_args()
    result={'workloads':[analyze(args.root/'native'/name,args.root/'profiles'/name,args.baseline,None if args.built_native_root is None else args.built_native_root/name) for name in WORKLOADS],'production_admitted':False}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print([(row['workload'],row['final_pixels_exact']) for row in result['workloads']])
