"""Separate indexed storage and binary alpha from nearest cache sampling."""
import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_rounded_footprint import prepare
from tools.probes.analyze_affine_scan_translation import vertices,fixed_scan
from tools.probes.build_bound_bitmap_component import ROOT


def decode(native):
    path=native/'fixture.json';raw=path.read_bytes() if path.exists() else gzip.decompress(path.with_suffix('.json.gz').read_bytes())
    fixture=json.loads(raw);build=json.loads((native/'build.json').read_text());assert hashlib.sha256(raw).hexdigest()==build['fixture_sha256']
    for a,b in [('source','source_sha256'),('harness_source','harness_sha256'),('builder_source','builder_sha256')]:assert hashlib.sha256((ROOT/build[a]).read_bytes()).hexdigest()==build[b]
    assert build['shape_and_other_tags_preserved'] and not build['raw_tags_preserved']
    synthetic=fixture['synthetic_source'];expected=[]
    for y in range(200):
        for x in range(137):
            a=255 if synthetic['alpha']=='opaque' else fixture['leaf']['pixels_premultiplied'][y*137+x][3]
            expected.append(([x,0,73,a] if synthetic['axis']=='x' else [0,y,73,a]) if a else [0]*4)
    assert synthetic['pixels_premultiplied']==expected
    source=[];cases=[]
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='source':
            assert int(v[0])==len(source)//137 and len(v)==275
            source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='case':
            assert len(v)==17 and int(v[0])==len(cases)
            phase=len(cases);assert v[1:3]==[str(phase//2),str(phase%2)] and v[15:]==['true' if phase%2 else 'false','0']
            properties=fixture['cases'][1];declared=properties[:6]+[1,0,0,1]+properties[6:]
            assert list(map(Fraction,v[3:15]))==[Fraction(format(float(z),'.15g')) for z in declared]
            cases.append({'key':v,'pixels':[]})
        elif kind=='row':
            pixels=cases[-1]['pixels'];assert int(v[0])==len(pixels)//600 and len(v)==1201
            pixels.extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert source==expected and len(cases)==4 and all(len(c['pixels'])==240000 for c in cases)
    return fixture,source,cases


def comparison(actual,native):
    failures=[];maximum=0
    for i,(p,q) in enumerate(zip(actual,native)):
        maximum=max(maximum,max(abs(a-b) for a,b in zip(p,q)))
        if p!=q:failures.append({'x':i%600,'y':i//600,'actual':p,'native':q})
    assert len(actual)==len(native)==240000
    return {'samples':240000,'exact':240000-len(failures),'max_channel_delta':maximum,'failures':failures}


def analyze(root):
    rows=[]
    for axis in ('x','y'):
        for alpha in ('opaque','original'):
            name=axis+'-'+alpha;fixture,source,cases=decode(root/name)
            key=cases[0]['key'][3:15];fixed=prepare(tuple(inverse_signed(['0']*5+key)),'ties_even')
            counts=fixed_scan(vertices(['0']*3+['137','200']+key),0,0,600,400,16,'trunc')
            predicted=[]
            for i,n in enumerate(counts):
                p=[0]*4
                if n:
                    x,y=i%600,i//600;ix,iy=((a*x+b*y+t+offset)//65536 for a,b,t,offset,_ in fixed)
                    p=[v*n//16 for v in source[max(0,min(199,iy))*137+max(0,min(136,ix))]]
                predicted.append(p)
            comparisons={}
            for cache in range(2):comparisons[f'indexed_vs_as/cache{cache}']=comparison(cases[cache]['pixels'],cases[cache+2]['pixels'])
            for storage in range(2):comparisons[f'cache_vs_uncached/storage{storage}']=comparison(cases[storage*2+1]['pixels'],cases[storage*2]['pixels'])
            for i,case in enumerate(cases):comparisons[f'uncached_model/case{i}']=comparison(predicted,case['pixels'])
            rows.append({'input':name,'source_texels_exact':len(source),'comparisons':comparisons})
    return {'rows':rows,'cache_initializer_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for row in r['rows']:print(row['input'],{k:(v['exact'],v['max_channel_delta']) for k,v in row['comparisons'].items()})
