"""Read original-tag controls in pinned Drawing API order, retaining raw property evidence."""
import gzip
import hashlib
import json
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.decode_jinye_affine_controls import source_pixel
from tools.probes.run_nested_filters import unpack


def decode(native):
    path=native/'fixture.json';fixture=json.loads(path.read_text());cases={};matrices={};sources=[]
    assert fixture==json.loads((ROOT/'evidence/importer-loud-fail/r222/native/fixture.json').read_text())
    source=fixture['source_graph']['source']
    assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256']
    for source_id in range(6):
        folder=native/f'source{source_id}';build=json.loads((folder/'build.json').read_text())
        assert build['source_id']==source_id and build['source_graph']==source
        assert hashlib.sha256(path.read_bytes()).hexdigest()==build['fixture_sha256']
        assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
        assert build['raw_shape_sha256']=={str(cid):fixture['source_graph']['raw_tag_sha256'][str(cid)] for cid in (56,57)}
        expected_ids=[c['id'] for c in fixture['cases'] if c['source']==source_id];assert build['case_ids']==expected_ids
        log=folder/'native.log';text=log.read_text() if log.exists() else gzip.decompress(log.with_suffix('.log.gz').read_bytes()).decode()
        events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
        assert len(events)==1212 and events[-1][6:]==['done','ok']
        pixels=[];seen=[];active=None
        for i,event in enumerate(events):
            assert event[1]==build['run_id'] and event[2:6]==[str(i),'0','0','0']
            kind,payload=event[6:];v=payload.split(',')
            if kind=='source_size':assert i==0 and v==['92','40']
            elif kind=='source':
                ci,y=map(int,v[:2]);assert ci==source_id and len(v)==94 and len(pixels)==y*92
                row=[[(int(p)>>shift)&255 for shift in (16,8,0,24)] for p in v[2:]]
                assert row==[source_pixel(ci,x,y) for x in range(92)];pixels.extend(row)
            elif kind=='matrix':
                assert len(v)==19 and int(v[0])==expected_ids[len(seen)]
                cid=int(v[0]);spec=fixture['cases'][cid];expected=spec['matrix']+spec['outer']+spec['draw']
                assert list(map(float,v[1:]))==[float(format(x,'.15g')) for x in expected]
                assert cid not in matrices;matrices[cid]=list(map(float,v));seen.append(cid)
            elif kind=='case':
                cid,mode=int(v[0]),int(v[1]);assert cid==seen[-1] and mode in (0,1)
                assert v[2:]==['true' if mode else 'false','0'] and (cid,mode) not in cases
                active={'source_case':cid,'cached':bool(mode),'pixels':[]};cases[cid,mode]=active
            elif kind=='row':
                assert active is not None and len(v)==193 and int(v[0])*96==len(active['pixels'])
                active['pixels'].extend(unpack(list(map(int,v[1:]))))
            else:assert kind=='done'
        assert seen==expected_ids and len(pixels)==3680
        assert hashlib.sha256(bytes(c for p in pixels for c in p)).hexdigest()==build['input_rgba_sha256']
        sources.append(pixels)
    ordered=[cases[i,mode] for i in range(36) for mode in (0,1)]
    assert len(cases)==72 and all(len(c['pixels'])==9216 for c in ordered)
    return fixture,sources,ordered,[matrices[i] for i in range(36)]
