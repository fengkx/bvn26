"""Validate one fixed edge slope on independent long signed parallelograms."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_affine_scan_translation import fixed_scan
from tools.probes.analyze_affine_scan_coverage import scan_coverage


def decode(native):
    source, cases = [], []
    for kind, payload in events(native):
        v = payload.split(',')
        if kind == 'source':
            assert int(v[0]) == len(source)//64 and len(v) == 129
            source.extend(unpack(list(map(int, v[1:]))))
        elif kind == 'case':
            assert len(v) == 32 and int(v[0]) == len(cases)
            cases.append({'key': v, 'pixels': []})
        elif kind == 'row':
            case = cases[-1]; left, top, width, height = map(int, case['key'][24:28])
            assert int(v[0]) == top + len(case['pixels'])//width and len(v) == 1+2*width
            case['pixels'].extend(unpack(list(map(int, v[1:]))))
        else:
            assert [kind, payload] == ['done', 'ok']
    assert source == [[144, 120, 8, 255]]*4096 and len(cases) == 64
    for case in cases:
        k = case['key']; left, top, w, h, ux, uy, uw, uh = map(int, k[24:32])
        assert len(case['pixels']) == w*h
        if not (0 <= left <= ux < ux+uw <= left+w <= 512 and 0 <= top <= uy < uy+uh <= top+h <= 512):
            raise ValueError(f'case{k[0]}: incomplete edge capture')
        points = list(map(Fraction, k[6:14])); xs, ys = points[::2], points[1::2]
        assert list(map(Fraction, k[14:18])) == [min(xs), max(xs), min(ys), max(ys)]
        assert list(map(Fraction, k[18:24])) == [1, 0, 0, 1, 0, 0]
        height, dx, phase = map(Fraction, k[3:6]); x, y = 150+phase, 10+phase
        assert points == [x,y,x+19,y,x+19+dx,y+height,x+dx,y+height]
    return cases


def analyze(native):
    cases = decode(native); scores, pairs = {}, []
    for i in range(0, len(cases), 2):
        a,b = cases[i:i+2]
        assert a['key'][1] == b['key'][1] and a['key'][3:28] == b['key'][3:28]
        pairs.append({'case':int(a['key'][1]), 'samples':len(a['pixels']),
                      'exact':sum(p==q for p,q in zip(a['pixels'],b['pixels']))})
    for case in cases:
        k=case['key']; left,top,width,height=map(int,k[24:28])
        values=list(map(Fraction,k[6:14])); points=list(zip(values[::2],values[1::2]))
        candidates={'exact/half_up':scan_coverage(points,left,top,width,height,0,0,'half_up')}
        for bits in (8,16,24):
            for mode in ('floor','even','trunc'):
                candidates[f'fixed{bits}/{mode}']=fixed_scan(points,left,top,width,height,bits,mode)
        for name,counts in candidates.items():
            s=scores.setdefault(name,{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]})
            for i,(count,pixel) in enumerate(zip(counts,case['pixels'])):
                actual=[v*count//16 for v in (144,120,8,255)]
                s['samples']+=1;s['exact']+=actual==pixel
                s['max_channel_delta']=max(s['max_channel_delta'],max(abs(p-q) for p,q in zip(actual,pixel)))
                if actual!=pixel:s['failures'].append({'case':int(k[0]),'x':left+i%width,'y':top+i//width,'actual':actual,'native':pixel})
    return {'source_texels_exact':4096,'cases':64,'bounds_and_properties_exact':64,
            'storage_pairs':pairs,'scores':scores,'coverage_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
