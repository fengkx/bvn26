"""Decode explicit source-leaf cache controls without using readbacks as input assets."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.run_nested_filters import unpack
from tools.probes.run_nearest_matrix_family import measure


def decode(native):
    build=json.loads((native/'build.json').read_text());path=native/'fixture.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==build['fixture_sha256']
    fixture=json.loads(path.read_text())
    assert hashlib.sha256((ROOT/build['source']['path']).read_bytes()).hexdigest()==build['source']['sha256']
    assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    path=native/'native.log';text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    assert len(events)==1607 and events[-1][6:]==['done','ok']
    cases=[];matrices=[]
    for i,event in enumerate(events):
        assert event[1]==build['run_id'] and event[2:6]==[str(i),'0','0','0']
        kind,payload=event[6:];v=payload.split(',')
        if kind=='matrix':
            assert len(v)==23 and int(v[0])==len(matrices)
            spec=fixture['cases'][len(matrices)]
            expected=spec['matrix']+spec['outer']+spec['draw']
            assert list(map(float,v[1:19]))==[float(format(x,'.15g')) for x in expected]
            matrices.append(list(map(float,v)))
        elif kind=='case':
            assert v==[str(len(cases)//2),str(len(cases)%2),'true' if len(cases)%2 else 'false','0','1']
            cases.append({'source_case':int(v[0]),'cached':v[2]=='true','pixels':[]})
        elif kind=='row':
            assert len(v)==1201 and int(v[0])*600==len(cases[-1]['pixels'])
            cases[-1]['pixels'].extend(unpack(list(map(int,v[1:]))))
        else: assert kind=='done'
    assert len(cases)==4 and len(matrices)==2 and all(len(c['pixels'])==240000 for c in cases)
    return fixture,cases,matrices


def analyze(native):
    fixture,cases,matrices=decode(native);rows=[]
    for i,spec in enumerate(fixture['cases']):
        clear,cached=cases[2*i:2*i+2]
        rows.append({'case':spec,'nonzero_clear':sum(p[3]>0 for p in clear['pixels']),
                     'nonzero_cached':sum(p[3]>0 for p in cached['pixels']),
                     **measure(clear['pixels'],cached['pixels'],600)})
    return {'cache_pairs':rows,'matrix_readbacks':matrices,'production_admitted':False,'leaf_sampler_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print([(v['exact'],v['samples'],v['max_channel_delta']) for v in r['cache_pairs']])
