"""Reject invalid native BitmapData before interpreting indexed source bytes or interpolation."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.build_bound_bitmap_component import ROOT


def analyze(native):
    build=json.loads((native/'build.json').read_text());assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    records=events(native);assert len(records)==2436;source=[];indexed_rows=[];samples=[[],[]];loaded=[]
    for kind,payload in records:
        v=payload.split(',')
        if kind=='source':
            assert len(v)==71 and int(v[0])==len(source)//35;source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='indexed_source':
            assert len(v)==71 and int(v[0])==len(indexed_rows);indexed_rows.append(list(map(int,v[1:])))
        elif kind=='loaded':loaded.append(v)
        elif kind in ('sample0','sample1'):
            epoch=int(kind[-1]);assert len(v)==16;key=list(map(float,v[:13]));assert key[0]==epoch*1152+len(samples[epoch]);assert v[13]=='false'
            samples[epoch].append({'key':key,'native':unpack(list(map(int,v[14:])))[0]})
        else:assert [kind,payload]==['done','ok']
    palette=[[0,0,0,0],[255,0,0,255],[0,255,0,255],[0,0,255,255]];expected=[palette[y%2*2+x%2] for y in range(65) for x in range(35)]
    assert source==expected and all(len(v)==1152 for v in samples) and len(indexed_rows)==65 and len(loaded)==1
    valid=loaded==[['35','65','true']]
    if valid:
        pixels=[p for row in indexed_rows for p in unpack(row)]
        source_result={'status':'valid','samples':2275,'exact':sum(a==b for a,b in zip(pixels,expected))}
    else:
        source_result={'status':'invalid_bitmap','properties':loaded[0],'raw_readbacks_not_interpreted':True}
    before_after=[];api=[]
    for a,b in zip(*samples):
        assert a['key'][1:]==b['key'][1:];before_after.append(a['native']==b['native'])
    for epoch,rows in enumerate(samples):
        diffs=[]
        for a,b in zip(rows[::2],rows[1::2]):
            assert a['key'][1]==0 and b['key'][1]==1 and a['key'][2:12]==b['key'][2:12]
            if a['native']!=b['native']:diffs.append({'indexed':a,'as':b})
        api.append({'epoch':epoch,'samples':576,'exact':576-len(diffs),'differences':diffs})
    return {'native_bitmap_properties':loaded[0],'as_source_exact':2275,'native_source':source_result,'before_after_exact':sum(before_after),'before_after_samples':1152,'api_comparisons':api,'native_indexed_source_verified':valid and source_result.get('exact')==2275,'indexed_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print(r['native_source']);print('before/after',r['before_after_exact'],1152);print('API',[(v['exact'],v['samples']) for v in r['api_comparisons']])
