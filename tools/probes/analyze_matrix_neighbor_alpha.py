"""Hold target bytes fixed while independently changing neighbor alpha and row geometry."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import struct
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.build_bound_bitmap_component import ROOT

COLORS=([160,128,8,255],[248,232,48,255])


def decode(native):
    matrix=None;cases=[]
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='matrix':assert matrix is None;matrix=list(map(float,v))
        elif kind=='case':
            key=list(map(int,v));assert len(key)==8 and key[0]==len(cases)
            cases.append({'key':key})
        elif kind in ('source','filtered'):
            case=cases[-1];assert kind not in case and len(v)==2*case['key'][1]
            case[kind]=unpack(list(map(int,v)))
        else:assert [kind,payload]==['done','ok']
    original=json.loads((ROOT/'evidence/importer-loud-fail/r195/native/frame3/build.json').read_text())['case']['placement']['filters'][0]['matrix']
    expected=[float(format(struct.unpack('<f',struct.pack('<f',v))[0],'.15g')) for v in original];assert matrix==expected
    assert len(cases)==2048
    for case in cases:
        _,w,base,lane,mask,neighbor_alpha,color,target=case['key'];assert target==base+lane and 0<=base<=w-4
        assert len(case['source'])==len(case['filtered'])==w
        expected_alpha=[255]*w;bit=0
        for j in range(4):
            if j==lane:continue
            expected_alpha[base+j]=neighbor_alpha if mask&(1<<bit) else 0;bit+=1
        assert [p[3] for p in case['source']]==expected_alpha
        for x,p in enumerate(case['source']):
            if expected_alpha[x]==255:assert p==COLORS[color]
            elif expected_alpha[x]==0:assert p==[0]*4
            else:assert all(0<=v<=127 for v in p[:3])
    return matrix,cases


def analyze(native):
    matrix,cases=decode(native);groups=defaultdict(list);observations=[]
    for case in cases:
        identity,w,base,lane,mask,neighbor_alpha,color,target=case['key'];pixel=case['filtered'][target]
        row={'case':identity,'width':w,'group_start':base,'lane':lane,'mask':mask,'neighbor_alpha':neighbor_alpha,'color':color,'target_x':target,
             'source_target':case['source'][target],'source_group':case['source'][base:base+4],'target_output':pixel}
        observations.append(row);groups[(w,base,lane,neighbor_alpha,color)].append(row)
    comparisons=[]
    for key,rows in groups.items():
        assert len(rows)==8 and sorted(v['mask'] for v in rows)==list(range(8))
        outputs=sorted(set(tuple(v['target_output']) for v in rows))
        comparisons.append({'width':key[0],'group_start':key[1],'lane':key[2],'neighbor_alpha':key[3],'color':key[4],
                            'distinct_outputs':[list(v) for v in outputs],'changed_by_neighbor_mask':len(outputs)>1})
    return {'cases':len(cases),'explicit_source_pixels':sum(len(c['source']) for c in cases),'target_source_exact':len(cases),
            'matrix_properties':matrix,'observations':observations,'groups':comparisons,
            'changed_target_groups':sum(v['changed_by_neighbor_mask'] for v in comparisons),
            'arithmetic_admitted':False,'partition_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native)
    a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print('targets',r['target_source_exact'],'neighbor-sensitive groups',r['changed_target_groups'],'/',len(r['groups']))
