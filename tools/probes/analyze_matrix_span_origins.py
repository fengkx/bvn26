"""Separate processed-span origins from neighboring color in native ColorMatrix controls."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import struct
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_matrix_neighbor_alpha import COLORS


def decode(native):
    matrix=None;cases=[]
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='matrix':assert matrix is None;matrix=list(map(float,v))
        elif kind=='case':
            key=list(map(int,v));assert len(key)==9 and key[0]==len(cases)
            cases.append({'key':key})
        elif kind in ('source','filtered'):
            assert kind not in cases[-1] and len(v)==128
            cases[-1][kind]=unpack(list(map(int,v)))
        else:assert [kind,payload]==['done','ok']
    original=json.loads((ROOT/'evidence/importer-loud-fail/r195/native/frame3/build.json').read_text())['case']['placement']['filters'][0]['matrix']
    assert matrix==[float(format(struct.unpack('<f',struct.pack('<f',v))[0],'.15g')) for v in original]
    assert len(cases)==1728
    for case in cases:
        _,w,sx,dx,at,mode,color,source_x,dest_x=case['key']
        assert 1<=w<=9 and sx in (0,1,3) and dx in (0,1,3) and 0<=at<w and source_x==sx+at and dest_x==dx+at
        fill=[COLORS[color],[0]*4,[0,255,0,255],[0,0,0,255]][mode]
        expected=[fill[:] for _ in range(64)];expected[source_x]=COLORS[color]
        assert case['source']==expected
        assert all(p==[0]*4 for x,p in enumerate(case['filtered']) if not dx<=x<dx+w)
    return matrix,cases


def summarize(groups,labels):
    rows=[]
    for key,values in groups.items():
        outputs=sorted(set(tuple(v['target_output']) for v in values))
        rows.append({**dict(zip(labels,key)),'cases':[v['case'] for v in values],
                     'distinct_outputs':[list(v) for v in outputs],'invariant':len(outputs)==1})
    return rows


def analyze(native):
    matrix,cases=decode(native);origins=defaultdict(list);colors=defaultdict(list);observations=[]
    for case in cases:
        identity,w,sx,dx,at,mode,color,source_x,dest_x=case['key']
        row={'case':identity,'width':w,'source_origin':sx,'destination_origin':dx,'target_offset':at,'neighbor_mode':mode,'color':color,
             'source_target':case['source'][source_x],'target_output':case['filtered'][dest_x]}
        observations.append(row);origins[(w,at,mode,color)].append(row)
        if mode in (0,2,3):colors[(w,sx,dx,at,color)].append(row)
    assert all(len(v)==9 for v in origins.values()) and all(len(v)==3 for v in colors.values())
    origin_rows=summarize(origins,('width','target_offset','neighbor_mode','color'))
    color_rows=summarize(colors,('width','source_origin','destination_origin','target_offset','color'))
    return {'cases':len(cases),'explicit_source_pixels':len(cases)*64,'matrix_properties':matrix,'observations':observations,
            'origin_groups':origin_rows,'opaque_neighbor_color_groups':color_rows,
            'origin_invariant_groups':sum(v['invariant'] for v in origin_rows),
            'neighbor_color_invariant_groups':sum(v['invariant'] for v in color_rows),
            'arithmetic_admitted':False,'partition_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native)
    a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print('origin invariant',r['origin_invariant_groups'],len(r['origin_groups']));print('neighbor color invariant',r['neighbor_color_invariant_groups'],len(r['opaque_neighbor_color_groups']))
