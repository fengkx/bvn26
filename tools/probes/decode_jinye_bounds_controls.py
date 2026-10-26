"""Strict native readback for enclosing-bounds-only controls."""
import gzip
import hashlib
import json
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.build_jinye_bounds_controls import controls
from tools.probes.build_jinye_sampling_modes import source_pixel
from tools.probes.decode_jinye_source_factorization import append_row,recover_linear_property


def decode(native):
    path=native/'fixture.json';fixture=json.loads(path.read_text());expected,tags=controls();assert fixture==expected
    sources=[];captures=[];matrices=[]
    for variant in fixture['variants']:
        folder=native/f"bounds{variant['id']}";build=json.loads((folder/'build.json').read_text());assert build['variant']==variant['id'] and build['raw_tags_unchanged_by_import'] is True
        assert hashlib.sha256(path.read_bytes()).hexdigest()==build['fixture_sha256']
        assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
        assert {str(cid):hashlib.sha256(raw).hexdigest() for cid,raw in tags[variant['id']].items()}==build['shape_sha256']
        log=folder/'native.log';text=log.read_text() if log.exists() else gzip.decompress(log.with_suffix('.log.gz').read_bytes()).decode()
        events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
        assert len(events)==1072 and events[-1][6:]==['done','ok']
        source=[];active=None;seen=[];local_captures=0
        for index,event in enumerate(events):
            assert event[1]==build['run_id'] and event[2:6]==[str(index),'0','0','0']
            kind,payload=event[6:];v=payload.split(',')
            if kind=='source_size':assert index==0 and v==['92','40']
            elif kind=='source':
                ci,y=map(int,v[:2]);assert ci==0 and len(v)==94 and len(source)==y*92 and 0<=y<40
                words=list(map(int,v[2:]));assert all(-(1<<31)<=word<(1<<32) for word in words)
                row=[[(word>>s)&255 for s in (16,8,0,24)] for word in words]
                assert row==[source_pixel(x,y) for x in range(92)];source.extend(row)
            elif kind=='matrix':
                assert len(source)==3680 and len(v)==23
                cid=int(v[0]);assert cid==build['case_ids'][len(seen)]
                if active is not None:assert len(active['pixels'])==65536
                case=fixture['cases'][cid];actual=list(map(float,v));expected=case['matrix']+case['outer']+case['draw']
                for i,(value,want) in enumerate(zip(actual[1:19],expected)):
                    if i%6<4:recover_linear_property(value,want)
                    else:assert value==want
                matrices.append(actual);seen.append(cid)
            elif kind=='case':
                if active is not None:assert len(active['pixels'])==65536
                cid,cache,clip=map(int,v[:3]);assert len(v)==14 and cid==seen[-1] and clip==0
                assert (cid,cache)==(build['case_ids'][local_captures//2],local_captures%2)
                assert v[3:6]==['omitted','true' if cache else 'false','0'] and list(map(float,v[6:10]))==[0,0,256,256]
                active={'source_case':cid,'cached':bool(cache),'clip_id':0,'clip':None,'bounds':list(map(float,v[10:])),'pixels':[],'black':[]};captures.append(active);local_captures+=1
            elif kind=='row':append_row(active,v)
            else:assert kind=='done' and index==len(events)-1
        assert len(source)==3680 and seen==build['case_ids'] and local_captures==4
        assert hashlib.sha256(bytes(c for p in source for c in p)).hexdigest()==build['input_rgba_sha256'];sources.append(source)
    assert len(sources)==13 and len(matrices)==26 and len(captures)==52
    assert all(len(c['pixels'])==65536 and len(c['black'])==65536 for c in captures)
    return fixture,sources,captures,matrices
