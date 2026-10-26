"""Test explicit parent-cache normalization across independent scale factors."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_width import ROOT
from tools.probes.analyze_bitmap_cache_scale_factors import analyze as prior_analyze


def analyze(native):
    build = json.loads((native / 'build.json').read_text())
    assert hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest() == build['source_sha256']
    p = native / 'native.log'
    text = p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows = [s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows) == 633 and rows[-1][6:] == ['done', 'ok']
    old = prior_analyze(ROOT / 'evidence/importer-loud-fail/r107/native')
    cases = []
    inputs = 0
    for i,r in enumerate(rows):
        assert r[1] == build['run_id'] and r[2:6] == [str(i), '0', '0', '0']
        kind,value = r[6:]
        if kind == 'source':
            label,width,y,*values = value.split(',')
            assert label == 'shared' and width == '16' and int(y) == inputs//16 and len(values)==16
            for x,v in enumerate(values):
                assert int(v)&0xffffffff == 0xff000000+x%2*255*65536+((x*37+17)%256)*256+113
                inputs+=1
        elif kind == 'case':
            key=list(map(float,value.split(',')))
            assert key == old['cases'][len(cases)]['key']
            cases.append({'key':key,'rows':[],'matrices':[]})
        elif kind == 'flags':
            assert value == ('0,false,false','1,true,false','2,false,true')[len(cases[-1]['rows'])]
        elif kind == 'pixels':
            values=[int(v)&0xffffffff for v in value.split(',')]
            assert values == old['cases'][len(cases)-1]['rows'][len(cases[-1]['rows'])]
            cases[-1]['rows'].append(values)
        elif kind == 'localMatrix':
            values=list(map(float,value.split(',')))
            assert len(values)==5 and values[0]==len(cases[-1]['matrices'])
            cases[-1]['matrices'].append(values)
        elif kind in ('local0','local1','placed0','placed1'):
            values=[int(v)&0xffffffff for v in value.split(',')]
            assert len(values)==(160 if kind.startswith('local') else 512) and kind not in cases[-1]
            cases[-1][kind]=values
        else:
            assert kind=='done'
    assert len(cases)==48 and inputs==128
    comparisons=[]
    for c in cases:
        assert len(c['rows'])==3 and len(c['matrices'])==2
        for mode in (0,1):
            origin=int(c['matrices'][mode][-1]);local=c['local'+str(mode)]
            copied=[local[x-origin] if 0<=x-origin<160 else 0 for x in range(512)]
            for name,right in [('integer_copy',copied),('parent_cache',c['rows'][2]),('child_cache',c['rows'][1])]:
                left=c['placed'+str(mode)]
                failed=[{'x':x,'actual_argb':a,'reference_argb':b} for x,(a,b) in enumerate(zip(left,right)) if a!=b]
                comparisons.append({'case':int(c['key'][0]),'mode':mode,'comparison':name,'samples':512,'exact':512-len(failed),'failures':failed})
    return {'input_exact':inputs,'prior_native_exact':48*3*512,'cases':cases,'comparisons':comparisons,'candidate_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for mode in (0,1):
        for name in ('integer_copy','parent_cache','child_cache'):
            rows=[v for v in r['comparisons'] if v['mode']==mode and v['comparison']==name]
            print(mode,name,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows))
