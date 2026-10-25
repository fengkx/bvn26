"""Compare fixed nearest affine initializers on geometry-selected interior controls."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


def decode(native):
    records=events(native);assert len(records)==6577;source=[];cases=[]
    for kind,payload in records:
        v=payload.split(',')
        if kind=='source':
            assert int(v[0])==len(source)//16 and len(v)==33;source.extend(unpack(list(map(int,v[1:]))))
        elif kind=='case':
            assert len(v)==17 and int(v[0])==len(cases);cases.append({'key':v,'pixels':[]})
        elif kind=='row':
            p=cases[-1]['pixels'];assert int(v[0])==len(p)//40 and len(v)==81;p.extend(unpack(list(map(int,v[1:]))))
        else:assert [kind,payload]==['done','ok']
    assert source==[[8+x*15,8+y*15,73,255] for y in range(16) for x in range(16)]
    assert len(cases)==160 and all(len(v['pixels'])==1600 for v in cases)
    return source,cases


def inverse(key):
    a,b,c,d,tx,ty=map(Fraction,key[5:11]);assert list(map(Fraction,key[11:15]))==[1,0,0,1]
    tx=Fraction(round(tx*4),4)+Fraction(math.trunc(Fraction(key[15])*4),4)
    ty=Fraction(round(ty*4),4)+Fraction(math.trunc(Fraction(key[16])*4),4)
    determinant=a*d-b*c;assert determinant>0
    return [(d/determinant,-c/determinant,(c*ty-d*tx)/determinant),(-b/determinant,a/determinant,(b*tx-a*ty)/determinant)]


def analyze(native):
    source,cases=decode(native);scores={};excluded=0
    for case in cases:
        coeff=inverse(case['key']);fixed=[[math.floor(v*65536+Fraction(1,2)) for v in row] for row in coeff]
        for y in range(40):
            for x in range(40):
                corners=[[a*xx+b*yy+t for a,b,t in coeff] for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1))]
                # A full source-texel margin separates sampling from unknown polygon coverage.
                if not all(1<=v<=15 for p in corners for v in p):excluded+=1;continue
                target=case['pixels'][y*40+x];assert target[3]==255
                routes={'exact_inverse_center':[math.floor(a*(x+Fraction(1,2))+b*(y+Fraction(1,2))+t) for a,b,t in coeff],
                        'fixed_inverse_center':[(a*x+b*y+t+round(Fraction(a+b,2)))//65536 for a,b,t in fixed]}
                for name,indices in routes.items():
                    ix,iy=indices;assert 0<=ix<16 and 0<=iy<16;actual=source[iy*16+ix]
                    r=scores.setdefault(name,{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]});r['samples']+=1;r['exact']+=actual==target;r['max_channel_delta']=max(r['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,target)))
                    if actual!=target:r['failures'].append({'key':case['key'],'x':x,'y':y,'indices':indices,'actual':actual,'native':target})
    return {'source_texels_exact':256,'cases':160,'scores':scores,'excluded_by_geometry':excluded,'affine_sampler_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
