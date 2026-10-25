"""Strictly retain source readbacks and geometry for independent affine controls."""
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.run_nested_filters import unpack


def source_pixel(ci,x,y):
    if ci==0:return [2*x,0,73,255]
    if ci==1:return [0,6*y,73,255]
    value=255 if (x,y)==(45+(ci-2)%2,19+(ci-2)//2) else 0
    return [value,value,value,255]


def decode(native):
    build=json.loads((native/'build.json').read_text());path=native/'fixture.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==build['fixture_sha256']
    fixture=json.loads(path.read_text());source=fixture['source_graph']['source']
    assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256']
    assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    path=native/'native.log';text=path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    assert len(events)==7261 and events[-1][6:]==['done','ok']
    sources=[[] for _ in range(6)];cases=[];matrices=[]
    for i,event in enumerate(events):
        assert event[1]==build['run_id'] and event[2:6]==[str(i),'0','0','0']
        kind,payload=event[6:];v=payload.split(',')
        if kind=='source':
            ci,y=map(int,v[:2]);assert 0<=ci<6 and len(v)==94 and len(sources[ci])==y*92
            pixels=[[(int(p)>>shift)&255 for shift in (16,8,0,24)] for p in v[2:]]
            assert pixels==[source_pixel(ci,x,y) for x in range(92)]
            sources[ci].extend(pixels)
        elif kind=='matrix':
            assert len(v)==25 and int(v[0])==len(matrices)
            spec=fixture['cases'][len(matrices)]
            expected=spec['fill']+spec['matrix']+spec['outer']+spec['draw']
            assert list(map(float,v[1:]))==[float(format(x,'.15g')) for x in expected]
            matrices.append(list(map(float,v)))
        elif kind=='case':
            assert v==[str(len(cases)//2),str(len(cases)%2),'true' if len(cases)%2 else 'false','0']
            cases.append({'source_case':int(v[0]),'cached':v[2]=='true','pixels':[]})
        elif kind=='row':
            assert len(v)==193 and int(v[0])*96==len(cases[-1]['pixels'])
            cases[-1]['pixels'].extend(unpack(list(map(int,v[1:]))))
        else: assert kind=='done'
    assert len(cases)==72 and len(matrices)==36 and all(len(c['pixels'])==9216 for c in cases)
    assert all(len(p)==92*40 for p in sources)
    return fixture,sources,cases,matrices
