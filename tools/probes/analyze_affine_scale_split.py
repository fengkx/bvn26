"""Require complete zero-phase images before using compensated scale paths as probes."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import struct
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


def property_float32(value):
    result=struct.unpack('<f',struct.pack('<f',float(value)))[0]
    assert float(format(result,'.15g'))==float(value)
    return Fraction(result)


def analyze(native,phase_native):
    records=events(native);assert len(records)==1642;source=[];cases=[]
    for kind,payload in records:
        v=payload.split(',')
        if kind=='source':assert int(v[0])==len(source)//16 and len(v)==33;source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='case':assert len(v)==29 and int(v[0])==len(cases);cases.append({'key':v,'pixels':[]})
        elif kind=='row':
            pixels=cases[-1]['pixels'];assert int(v[0])==96+len(pixels)//64 and len(v)==129;pixels.extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert source==[[x,y,73,255] for y in range(16) for x in range(16)] and len(cases)==25 and all(len(v['pixels'])==4096 for v in cases)
    groups={};rows=[];failures=[]
    for case in cases:
        k=case['key'];phase,factor=map(int,k[1:3]);assert factor in (1,4,16,64,128)
        cm=list(map(property_float32,k[3:9]));assert cm[4:]==[0,0]
        assert list(map(Fraction,k[9:15]))==[factor,0,0,factor,0,0] and list(map(Fraction,k[15:21]))==[1,0,0,1,128,128]
        assert list(map(Fraction,k[21:25]))==[0,0,16*factor,16*factor]
        x,y,w,h=map(int,k[25:]);assert w>0 and h>0 and 96<=x<x+w<=160 and 96<=y<y+h<=160
        g=groups.setdefault(phase,{});assert factor not in g;g[factor]=case
        case['effective_linear']=[str(v*factor) for v in cm[:4]]
    for phase,g in groups.items():
        assert set(g)=={1,4,16,64,128};base=g[1]
        for factor,case in g.items():
            assert case['effective_linear']==base['effective_linear']
            exact=sum(a==b for a,b in zip(case['pixels'],base['pixels']));delta=max(abs(v-w) for a,b in zip(case['pixels'],base['pixels']) for v,w in zip(a,b))
            rows.append({'phase':phase,'factor':factor,'effective_linear':case['effective_linear'],'used_bounds':case['key'][25:],'samples':4096,'exact':exact,'max_channel_delta':delta})
            for i,(a,b) in enumerate(zip(case['pixels'],base['pixels'])):
                if a!=b:failures.append({'phase':phase,'factor':factor,'x':i%64+96,'y':i//64+96,'actual':a,'baseline':b})
    old_exact=old_samples=0
    for kind,payload in events(phase_native):
        if kind!='sample':continue
        v=payload.split(',')
        if v[3]!='0':continue
        phase=int(v[1]);x,y=map(int,v[21:23]);pixel=unpack(list(map(int,v[23:])))[0]
        old_samples+=1;old_exact+=groups[phase][1]['pixels'][(y-96)*64+x-96]==pixel
    assert old_samples==30
    return {'source_texels_exact':256,'old_zero_phase':{'samples':old_samples,'exact':old_exact},'rows':rows,'failures':failures,'zero_phase_scale_paths_exact':not failures and old_exact==old_samples,'affine_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--phase-native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native,a.phase_native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print(r['old_zero_phase']);print('exact',sum(v['exact'] for v in r['rows']),sum(v['samples'] for v in r['rows']));print('gate',r['zero_phase_scale_paths_exact']);raise SystemExit(0 if r['zero_phase_scale_paths_exact'] else 1)
