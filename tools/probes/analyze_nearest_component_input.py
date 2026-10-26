"""Compare original indexed nearest input without discarding masks or transparent texels."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_rounded_footprint import indices
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_jiraiya_filter_boundary import comparison
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.run_nested_filters import unpack


def decode(native):
    path=native/'fixture.json';raw=path.read_bytes() if path.exists() else gzip.decompress(path.with_suffix('.json.gz').read_bytes())
    fixture=json.loads(raw);build=json.loads((native/'build.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==build['fixture_sha256']
    assert hashlib.sha256((ROOT/build['source']).read_bytes()).hexdigest()==build['source_sha256']
    assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    source=[];cases=[];source_size=None
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='sourceSize':assert source_size is None;source_size=list(map(int,v))
        elif kind=='source':
            assert int(v[0])==len(source)//137 and len(v)==275
            source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='case':
            assert len(v)==15 and int(v[0])==len(cases)
            cases.append({'key':v,'pixels':[]})
        elif kind=='row':
            p=cases[-1]['pixels'];assert int(v[0])==len(p)//600 and len(v)==1201
            p.extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert source_size==[137,200] and source==fixture['leaf']['pixels_premultiplied']
    assert len(cases)==6 and all(len(v['pixels'])==240000 for v in cases)
    return fixture,source,cases


def analyze(native,output_images=None):
    fixture,source,cases=decode(native);rows=[];failures=[]
    if output_images:output_images.mkdir(parents=True,exist_ok=True)
    for ci in range(2):
        before,after,materialized=(cases[ci+2*i] for i in range(3))
        assert before['key'][2:]==after['key'][2:]==materialized['key'][2:]
        co=inverse_signed(['0']*5+before['key'][3:15]);checks={name:{'samples':0,'exact':0,'max_channel_delta':[0]*4} for name in ('indexed','materialized')}
        unproven_nonzero=[]
        for y in range(400):
            for x in range(600):
                # Geometry alone selects fully covered pixels; source/native alpha never does.
                if not all(1<=a*x+b*y+t+min(0,a)+min(0,b) and a*x+b*y+t+max(0,a)+max(0,b)<=limit-1
                           for (a,b,t),limit in zip(co,(137,200))):
                    pixel=before['pixels'][y*600+x]
                    if pixel[3]:unproven_nonzero.append({'x':x,'y':y,'native':pixel})
                    continue
                ix,iy=indices(co,x,y,'ties_even');assert 0<=ix<137 and 0<=iy<200
                actual=source[iy*137+ix]
                for name,target in (('indexed',before),('materialized',materialized)):
                    pixel=target['pixels'][y*600+x];r=checks[name];r['samples']+=1;r['exact']+=actual==pixel
                    r['max_channel_delta']=[max(v,abs(a-b)) for v,a,b in zip(r['max_channel_delta'],actual,pixel)]
                    if actual!=pixel:failures.append({'case':ci,'storage':name,'x':x,'y':y,'source_indices':[ix,iy],'actual':actual,'native':pixel})
        rows.append({'case':ci,'matrix_readbacks':before['key'][3:15],
                     'before_after_load':comparison(before['pixels'],after['pixels']),
                     'indexed_vs_materialized':comparison(before['pixels'],materialized['pixels']),
                     'interior':checks,'unproven_nonzero_pixels':unproven_nonzero,'excluded_from_sampler_claim':240000-checks['indexed']['samples']})
        if output_images:
            for name,spec in (('before',before),('after',after),('materialized',materialized)):
                Image.frombytes('RGBA',(600,400),bytes(c for p in spec['pixels'] for c in p)).save(output_images/f'{ci}-{name}.png')
    return {'source_texels_exact':len(source),'raw_tags_preserved':True,'rows':rows,'failures':failures,
            'source_sampler_admitted':False,'production_admitted':False,'full_production_suite_rerun':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--images',type=Path);a=p.parse_args()
    r=analyze(a.native,a.images);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for v in r['rows']:
        print(v['case'],'load',v['before_after_load']['exact'],'storage',v['indexed_vs_materialized']['exact'],'interior',v['interior'])
