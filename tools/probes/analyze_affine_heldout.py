"""Apply fixed footprint constructions to independently authored affine matrices."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path

from tools.probes.analyze_affine_footprint import FAMILIES, indices
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


def inverse_signed(key):
    a,b,c,d,tx,ty = map(Fraction,key[5:11])
    assert list(map(Fraction,key[11:15])) == [1,0,0,1]
    tx = Fraction(round(tx*4),4) + Fraction(math.trunc(Fraction(key[15])*4),4)
    ty = Fraction(round(ty*4),4) + Fraction(math.trunc(Fraction(key[16])*4),4)
    determinant = a*d-b*c
    assert determinant != 0
    return [(d/determinant,-c/determinant,(c*ty-d*tx)/determinant),
            (-b/determinant,a/determinant,(b*tx-a*ty)/determinant)]


def analyze(native):
    source, samples, scores = [], [], {}
    for kind,payload in events(native):
        v = payload.split(',')
        if kind == 'source':
            assert int(v[0]) == len(source)//128 and len(v) == 257
            source.extend(unpack(list(map(int,v[1:]))))
        elif kind == 'sample':
            assert len(v) == 23 and int(v[0]) == len(samples)
            samples.append((v[:21],unpack(list(map(int,v[21:])))[0]))
        else:
            assert [kind,payload] == ['done','ok']
    assert source == [[x,y,73,255] for y in range(128) for x in range(128)]
    assert len(samples) == 2048
    for k,pixel in samples:
        assert pixel[2:] == [73,255]
        co = inverse_signed(k[:17])
        x,y = map(int,k[19:21])
        assert all(1 <= a*xx+b*yy+t <= 127 for a,b,t in co for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1)))
        for family in FAMILIES:
            actual = indices(co,x,y,family)+[73,255]
            group = 'reflected' if int(k[1]) >= 16 else 'positive'
            s = scores.setdefault(group+'/'+family,{'samples':0,'exact':0,'max_source_index_delta':0,'failures':[]})
            s['samples'] += 1
            s['exact'] += actual == pixel
            s['max_source_index_delta'] = max(s['max_source_index_delta'],max(abs(a-b) for a,b in zip(actual,pixel)))
            if actual != pixel:
                s['failures'].append({'key':k,'actual':actual,'native':pixel})
    return {'source_texels_exact':16384,'samples':2048,'scores':scores,
            'candidate_admitted':False,'gpu_advance_allowed':False,'production_admitted':False}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native)
    a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_source_index_delta'])
