"""Retain binary fill-translation provenance separately from native display readbacks."""
import gzip
import hashlib
import json
import struct
from tools.probes.build_bound_bitmap_component import ROOT,source_tags
from tools.probes.build_jinye_fill_translation_controls import controls,changed_tag
from tools.probes.build_jinye_sampling_modes import source_pixel
from tools.probes.decode_jinye_clip_controls import append_row,require_clear_outside


def decode(native):
    path=native/'fixture.json';fixture=json.loads(path.read_text());captures={};matrices=[];sources=[]
    graph,cases,variants=controls();assert fixture['cases']==cases and fixture['source_graph']==graph and fixture['variants']==variants
    assert fixture['size']==[96,96]
    source=graph['source'];assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256']
    raw={struct.unpack_from('<H',p)[0]:(p,r) for code,p,r in source_tags(ROOT/source['path']) if code==2 and struct.unpack_from('<H',p)[0] in (56,57)}
    for variant in variants:
        variant_id=variant['id'];ids=[c['id'] for c in cases if c['fill_variant']==variant_id]
        folder=native/f'fill{variant_id}';build=json.loads((folder/'build.json').read_text())
        assert build['variant']==variant and build['source_graph']==source and build['case_ids']==ids
        assert hashlib.sha256(path.read_bytes()).hexdigest()==build['fixture_sha256']
        assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
        for cid,(p,r) in raw.items():
            changed,metadata=changed_tag(p,r,variant['axis'],variant['delta'])
            assert build['changes'][str(cid)]==metadata
            assert build['original_shape_sha256'][str(cid)]==hashlib.sha256(r).hexdigest()
            assert build['shape_sha256'][str(cid)]==hashlib.sha256(changed).hexdigest()
            for spec in (c for c in cases if c['fill_variant']==variant_id and c['shape']==cid):
                assert [int(spec['fill_matrix'][k]) for k in ('translateX','translateY')]==[field['value'] for field in metadata['after'][1]['translations']]
        log=folder/'native.log';text=log.read_text() if log.exists() else gzip.decompress(log.with_suffix('.log.gz').read_bytes()).decode()
        events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
        assert len(events)==42+195*len(ids) and events[-1][6:]==['done','ok']
        pixels=[];seen=[];active=None
        for i,event in enumerate(events):
            assert event[1]==build['run_id'] and event[2:6]==[str(i),'0','0','0']
            kind,payload=event[6:];v=payload.split(',')
            if kind=='source_size':assert i==0 and v==['92','40']
            elif kind=='source':
                ci,y=map(int,v[:2]);assert ci==0 and len(v)==94 and len(pixels)==y*92
                row=[[(int(p)>>shift)&255 for shift in (16,8,0,24)] for p in v[2:]]
                assert row==[source_pixel(x,y) for x in range(92)];pixels.extend(row)
            elif kind=='matrix':
                assert len(v)==23 and int(v[0])==ids[len(seen)]
                cid=int(v[0]);spec=cases[cid];expected=spec['matrix']+spec['outer']+spec['draw']
                assert list(map(float,v[1:19]))==[float(format(x,'.15g')) for x in expected]
                matrices.append({'fill_variant':variant_id,'values':list(map(float,v))});seen.append(cid)
            elif kind=='case':
                assert len(v)==14
                cid,cache,clip_id=map(int,v[:3]);assert cid==seen[-1] and cache in (0,1) and clip_id==0
                clip=None;assert v[3]=='omitted'
                assert v[4:6]==['true' if cache else 'false','0']
                assert list(map(float,v[6:10]))==(clip if clip is not None else [0,0,96,96])
                key=cid,cache;assert key not in captures
                active={'fill_variant':variant_id,'source_case':cid,'cached':bool(cache),'clip_id':clip_id,'clip':clip,'bounds':list(map(float,v[10:])),'pixels':[]}
                captures[key]=active
            elif kind=='row':append_row(active,v)
            else:assert kind=='done'
        assert seen==ids and len(pixels)==3680
        assert hashlib.sha256(bytes(c for p in pixels for c in p)).hexdigest()==build['input_rgba_sha256']
        sources.append(pixels)
    ordered=[captures[i,cache] for i in range(100) for cache in (0,1)]
    assert len(captures)==200 and all(len(c['pixels'])==9216 for c in ordered)
    for capture in ordered:require_clear_outside(capture)
    return fixture,sources,ordered,matrices
