"""Read clip-only controls while retaining omitted versus explicit arguments."""
import gzip
import hashlib
import json
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.build_jinye_clip_controls import controls
from tools.probes.decode_jinye_affine_controls import source_pixel
from tools.probes.run_nested_filters import unpack


def append_row(active, values):
    assert active is not None and len(values)==193 and int(values[0])*96==len(active['pixels'])
    active['pixels'].extend(unpack(list(map(int,values[1:]))))


def require_clear_outside(capture):
    if capture['clip'] is None:return
    x,y,w,h=capture['clip'];failures=[]
    for i,p in enumerate(capture['pixels']):
        px,py=i%96,i//96
        if not (x<=px<x+w and y<=py<y+h) and any(p):failures.append([px,py,p])
    if failures:raise ValueError(f"Nonclear outside clip: case{capture['source_case']} cache{capture['cached']} clip{capture['clip_id']}: {len(failures)} pixels, first={failures[0]}")


def decode(native):
    path=native/'fixture.json';fixture=json.loads(path.read_text());captures={};matrices={};sources=[]
    graph,generated,clips=controls();assert fixture['cases']==generated and fixture['source_graph']==graph and fixture['clips']==clips
    assert fixture['size']==[96,96]
    source=graph['source'];assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256']
    for source_id in range(6):
        folder=native/f'source{source_id}';build=json.loads((folder/'build.json').read_text())
        assert build['source_id']==source_id and build['source_graph']==source
        assert hashlib.sha256(path.read_bytes()).hexdigest()==build['fixture_sha256']
        assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
        assert build['raw_shape_sha256']=={str(cid):graph['raw_tag_sha256'][str(cid)] for cid in (56,57)}
        ids=[c['id'] for c in generated if c['source']==source_id];assert build['case_ids']==ids
        log=folder/'native.log';text=log.read_text() if log.exists() else gzip.decompress(log.with_suffix('.log.gz').read_bytes()).decode()
        events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
        assert len(events)==13238 and events[-1][6:]==['done','ok']
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
                assert len(v)==23 and int(v[0])==ids[len(seen)]
                cid=int(v[0]);spec=generated[cid]
                expected=spec['matrix']+spec['outer']+spec['draw']
                assert list(map(float,v[1:19]))==[float(format(x,'.15g')) for x in expected]
                assert cid not in matrices;matrices[cid]=list(map(float,v));seen.append(cid)
            elif kind=='case':
                assert len(v)==14
                cid,mode,clip_id=map(int,v[:3]);assert cid==seen[-1] and mode in (0,1) and 0<=clip_id<len(clips)
                clip=clips[clip_id];assert v[3]==('omitted' if clip is None else 'rectangle')
                assert v[4:6]==['true' if mode else 'false','0']
                assert list(map(float,v[6:10]))==(clip if clip is not None else [0,0,96,96])
                key=cid,mode,clip_id;assert key not in captures
                active={'source_case':cid,'cached':bool(mode),'clip_id':clip_id,'clip':clip,'bounds':list(map(float,v[10:])),'pixels':[]}
                captures[key]=active
            elif kind=='row':append_row(active,v)
            else:assert kind=='done'
        assert seen==ids and len(pixels)==3680
        assert hashlib.sha256(bytes(c for p in pixels for c in p)).hexdigest()==build['input_rgba_sha256']
        sources.append(pixels)
    ordered=[captures[i,mode,clip] for i in range(24) for mode in (0,1) for clip in range(17)]
    assert len(captures)==816 and all(len(c['pixels'])==9216 for c in ordered)
    for capture in ordered:require_clear_outside(capture)
    return fixture,sources,ordered,[matrices[i] for i in range(24)]
