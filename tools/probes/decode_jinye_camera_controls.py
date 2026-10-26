"""Strictly read independently encoded affine factorization controls."""
import gzip
import hashlib
import json
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.build_jinye_camera_controls import controls
from tools.probes.build_jinye_sampling_modes import source_pixel
from tools.probes.jinye_source_factorization_tags import parse as parse_shape


from tools.probes.decode_jinye_source_factorization import recover_linear_property


def append_row(active, values):
    assert active is not None and len(values)==513
    y=int(values[0]);assert 0<=y<256 and len(active['pixels'])==y*256
    for x in range(256):
        raw,black=map(int,values[1+2*x:3+2*x]);assert all(-(1<<31)<=n<(1<<32) for n in (raw,black))
        pixel=[(raw>>s)&255 for s in (16,8,0,24)]
        assert (black>>24)&255==255
        # Both readbacks are retained; black composition is not source texture data.
        active['pixels'].append(pixel);active['black'].append([(black>>s)&255 for s in (16,8,0,24)])


def decode(native):
    path=native/'fixture.json';fixture=json.loads(path.read_text());assert fixture==controls()
    build=json.loads((native/'build.json').read_text());assert build['raw_tags_unchanged_by_import'] is True
    assert hashlib.sha256(path.read_bytes()).hexdigest()==build['fixture_sha256']
    assert hashlib.sha256((ROOT/build['harness_source']).read_bytes()).hexdigest()==build['harness_sha256']
    for shape in fixture['shapes']:
        raw=bytes.fromhex(shape['raw_tag_hex']);parsed=parse_shape(raw)
        assert parsed==shape['parsed'] and hashlib.sha256(raw).hexdigest()==shape['raw_tag_sha256']==build['shape_sha256'][str(parsed['shape'])]
    log=native/'native.log';text=log.read_text() if log.exists() else gzip.decompress(log.with_suffix('.log.gz').read_bytes()).decode()
    events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    assert len(events)==36092 and events[-1][6:]==['done','ok']
    source=[];captures=[];matrices=[];active=None
    for index,event in enumerate(events):
        assert event[1]==build['run_id'] and event[2:6]==[str(index),'0','0','0']
        kind,payload=event[6:];v=payload.split(',')
        if kind=='source_size':assert index==0 and v==['92','40']
        elif kind=='source':
            ci,y=map(int,v[:2]);assert ci==0 and len(v)==94 and len(source)==y*92 and 0<=y<40
            row=[[(int(p)>>s)&255 for s in (16,8,0,24)] for p in v[2:]]
            assert row==[source_pixel(x,y) for x in range(92)];source.extend(row)
        elif kind=='matrix':
            assert len(source)==3680 and len(v)==23 and int(v[0])==len(matrices)
            if active is not None:assert len(active['pixels'])==65536
            case=fixture['cases'][int(v[0])];actual=list(map(float,v))
            expected=case['matrix']+case['outer']+case['draw']
            for i,(value,want) in enumerate(zip(actual[1:19],expected)):
                if i%6<4:
                    recover_linear_property(value,want)
                else:assert value==want
            matrices.append(actual)
        elif kind=='case':
            if active is not None:assert len(active['pixels'])==65536
            cid,cache,clip=map(int,v[:3]);assert len(v)==14 and cid==len(matrices)-1 and clip==0
            assert (cid,cache)==(len(captures)//2,len(captures)%2)
            assert v[3:6]==['omitted','true' if cache else 'false','0'] and list(map(float,v[6:10]))==[0,0,256,256]
            active={'source_case':cid,'cached':bool(cache),'clip_id':0,'clip':None,'bounds':list(map(float,v[10:])),'pixels':[],'black':[]};captures.append(active)
        elif kind=='row':append_row(active,v)
        else:assert kind=='done' and index==len(events)-1
    assert len(source)==3680 and len(matrices)==70 and len(captures)==140
    assert all(len(c['pixels'])==65536 and len(c['black'])==65536 for c in captures)
    assert hashlib.sha256(bytes(c for p in source for c in p)).hexdigest()==build['input_rgba_sha256']
    return fixture,source,captures,matrices
