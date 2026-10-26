"""Measure clip-length effects with fixed source bytes, transforms and target pixels."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_nearest_affine import decode as decode_full,inverse


def analyze(native,full_native):
    source,full=decode_full(full_native);lookup={tuple(c['key'][1:]):c for c in full}
    records=events(native);assert len(records)==11537;raw=[];cases=[]
    for kind,payload in records:
        v=payload.split(',')
        if kind=='source':
            assert int(v[0])==len(raw)//16 and len(v)==33;raw.extend(unpack(list(map(int,v[1:]))))
        elif kind=='sample':
            assert len(v)==20 and int(v[0])==len(cases);cases.append({'key':v,'pixels':[]})
        elif kind=='pixels':
            case=cases[-1];assert not case['pixels'] and len(v)==int(case['key'][19])*2;case['pixels']=unpack(list(map(int,v)))
        else:assert [kind,payload]==['done','ok']
    assert raw==source and len(cases)==5760
    scores={};full_score={'samples':0,'exact':0,'interior_samples':0,'interior_exact':0,'max_channel_delta':0,'failures':[]};groups={}
    for case in cases:
        k=case['key'];original=lookup[tuple(k[1:17])];coeff=inverse(k[:17]);fixed=[[math.floor(v*65536+Fraction(1,2)) for v in row] for row in coeff]
        left,y,length=map(int,k[17:]);group=groups.setdefault(tuple(k[1:19]),{})
        assert length not in group;group[length]=case['pixels']
        for offset,target in enumerate(case['pixels']):
            x=left+offset;prior=original['pixels'][y*40+x];corners=[[a*xx+b*yy+t for a,b,t in coeff] for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1))];interior=all(1<=v<=15 for p in corners for v in p)
            full_score['samples']+=1;full_score['exact']+=target==prior;full_score['max_channel_delta']=max(full_score['max_channel_delta'],max(abs(a-b) for a,b in zip(target,prior)))
            if interior:full_score['interior_samples']+=1;full_score['interior_exact']+=target==prior
            if target!=prior:full_score['failures'].append({'key':k,'x':x,'interior':interior,'clip':target,'full':prior})
            if not interior:continue
            assert target[3]==255
            routes={'exact_inverse_center':[math.floor(a*(x+Fraction(1,2))+b*(y+Fraction(1,2))+t) for a,b,t in coeff],'fixed_inverse_center':[(a*x+b*y+t+round(Fraction(a+b,2)))//65536 for a,b,t in fixed]}
            for name,(ix,iy) in routes.items():
                actual=source[iy*16+ix];r=scores.setdefault(f'{name}/length{length}',{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]});r['samples']+=1;r['exact']+=actual==target;r['max_channel_delta']=max(r['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,target)))
                if actual!=target:r['failures'].append({'key':k,'x':x,'indices':[ix,iy],'actual':actual,'native':target})
    changed=[]
    for k,g in groups.items():
        assert sorted(g)==[1,3,4,8]
        for offset in range(4):
            observed={length:values[offset] for length,values in g.items() if offset<length}
            if len({tuple(v) for v in observed.values()})>1:changed.append({'key':list(k),'offset':offset,'pixels':observed})
    return {'source_texels_exact':256,'cases':5760,'full_row_comparison':full_score,'scores':scores,'length_changed_overlaps':changed,'affine_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--full-native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native,a.full_native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print('full', {k:v for k,v in r['full_row_comparison'].items() if k!='failures'});print('changed overlaps',len(r['length_changed_overlaps']))
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
