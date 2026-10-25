"""Reject common coefficient/byte conversions using independently controlled alpha contexts."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import struct
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.build_bound_bitmap_component import ROOT


def f32(value):
    return struct.unpack('<f',struct.pack('<f',value))[0]


def decode(native):
    cases=[]
    for kind,payload in events(native):
        v=payload.split(',')
        if kind=='case':
            key=list(map(int,v));assert len(key)==5 and key[0]==len(cases)
            cases.append({'key':key})
        elif kind=='matrix':
            assert kind not in cases[-1] and len(v)==20;cases[-1][kind]=list(map(float,v))
        elif kind in ('source','filtered'):
            assert kind not in cases[-1] and len(v)==8;cases[-1][kind]=unpack(list(map(int,v)))
        else:assert [kind,payload]==['done','ok']
    original=json.loads((ROOT/'evidence/importer-loud-fail/r195/native/frame3/build.json').read_text())['case']['placement']['filters'][0]['matrix']
    coefficients=[float(format(f32(original[row*5+axis]),'.15g')) for row in range(3) for axis in range(3)]
    assert len(cases)==4608
    for case in cases:
        _,ci,axis,value,neighbor=case['key'];assert axis==ci%3 and neighbor in (0,255)
        coefficient=coefficients[ci];offset=128 if coefficient<0 else 0
        matrix=[0,0,0,0,offset,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0];matrix[axis]=coefficient;assert case['matrix']==matrix
        target=[0,0,0,255];target[axis]=value
        assert case['source']==[target,[0,0,0,neighbor],[0]*4,[0]*4]
    return coefficients,cases


def red(value,coefficient,offset,precision,conversion):
    if precision=='stored32':coefficient=f32(coefficient)
    else:
        bits,quantization=precision.split('/');scale=1<<int(bits)
        coefficient={'trunc':math.trunc,'floor':math.floor,'even':round}[quantization](coefficient*scale)/scale
    result=coefficient*value+offset
    if conversion=='nearest':result=math.floor(result+.5)
    elif conversion=='floor':result=math.floor(result)
    else:
        assert conversion=='f32_nearest';result=math.floor(f32(f32(coefficient*value)+offset)+.5)
    return max(0,min(255,result))


def analyze(native):
    coefficients,cases=decode(native);scores={};rows=[]
    families=['stored32']+[f'{bits}/{mode}' for bits in (8,9,10,16) for mode in ('trunc','floor','even')]
    unchanged={'samples':0,'exact':0,'failures':[]}
    for case in cases:
        i,ci,axis,value,neighbor=case['key'];coefficient=coefficients[ci];offset=case['matrix'][4];target=case['filtered'][0]
        rows.append({'case':i,'coefficient_index':ci,'coefficient':coefficient,'axis':axis,'value':value,'neighbor_alpha':neighbor,
                     'input':case['source'][0],'target':target})
        unchanged['samples']+=1;same=target[1:]==case['source'][0][1:];unchanged['exact']+=same
        if not same:unchanged['failures'].append({'case':i,'input':case['source'][0],'target':target})
        for family in families:
            for conversion in ('nearest','floor','f32_nearest'):
                key=f'{neighbor}/{family}/{conversion}';s=scores.setdefault(key,{'samples':0,'exact_red':0,'max_red_delta':0,'failures':[]})
                actual=red(value,coefficient,offset,family,conversion);s['samples']+=1;s['exact_red']+=actual==target[0];s['max_red_delta']=max(s['max_red_delta'],abs(actual-target[0]))
                if actual!=target[0]:s['failures'].append({'case':i,'actual':actual,'native':target[0]})
    return {'cases':len(cases),'source_pixels_exact':len(cases)*4,'coefficients':coefficients,'rows':rows,'scores':scores,
            'identity_other_channels':unchanged,'arithmetic_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native)
    a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print('identity',r['identity_other_channels']['exact'],r['identity_other_channels']['samples'])
    for neighbor in (0,255):
        best=sorted(((v['exact_red'],k) for k,v in r['scores'].items() if k.startswith(str(neighbor)+'/')),reverse=True)
        print(neighbor,best[:8])
