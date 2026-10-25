"""Compare fixed vertex quantization and top-left scan coverage globally."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_affine_mask_coverage import decode


VERTICES=('exact','quarter_floor','quarter_even','quarter_half_up','quarter_ceil')


def polygon(key,family):
    width,height=map(int,key[3:5]);a,b,c,d,tx,ty=map(Fraction,key[5:11]);dx,dy=map(Fraction,key[15:17])
    tx=Fraction(round(tx*4),4)+Fraction(math.trunc(dx*4),4)
    ty=Fraction(round(ty*4),4)+Fraction(math.trunc(dy*4),4)
    vertices=[(a*x+c*y+tx,b*x+d*y+ty) for x,y in ((0,0),(width,0),(width,height),(0,height))]
    def quantize(v):
        if family=='exact':return v
        q={'quarter_floor':math.floor,'quarter_even':round,'quarter_half_up':lambda z:math.floor(z+Fraction(1,2)),'quarter_ceil':math.ceil}[family]
        return Fraction(q(v*4),4)
    return [(quantize(x),quantize(y)) for x,y in vertices]


def scan_coverage(vertices,left,top,width,height,phase_x,phase_y,round_x=None):
    assert phase_x in (0,1) and phase_y in (0,1)
    result=[0]*(width*height)
    edges=list(zip(vertices,vertices[1:]+vertices[:1]))
    for y in range(top,top+height):
        for sub in range(4):
            yy=Fraction(8*y+2*sub+phase_y,8);xs=[]
            for (ax,ay),(bx,by) in edges:
                if min(ay,by)<=yy<max(ay,by):xs.append(ax+(yy-ay)*(bx-ax)/(by-ay))
            assert len(xs) in (0,2)
            if not xs:continue
            lo,hi=sorted(xs)
            if round_x is None:
                start=math.ceil((lo*8-phase_x)/2);end=math.ceil((hi*8-phase_x)/2)
            else:
                assert round_x in ('half_up','even')
                quantize=(lambda v:math.floor(v+Fraction(1,2))) if round_x=='half_up' else round
                start=quantize(lo*4);end=quantize(hi*4)
            for x in range(left,left+width):
                result[(y-top)*width+x-left]+=max(0,min(4*x+4,end)-max(4*x,start))
    assert all(0<=v<=16 for v in result)
    return result


def analyze(native):
    cases=decode(native);scores={}
    for case in cases:
        k=case['key'];left,top,w,h=map(int,k[17:21])
        for family in VERTICES:
            vertices=polygon(k,family)
            for phase_x,phase_y,label,round_x in ((0,0,'lower',None),(1,1,'center',None),(1,0,'x_center_y_lower',None),(0,1,'x_lower_y_center',None),(0,0,'scan_half_up','half_up'),(0,0,'scan_even','even')):
                counts=scan_coverage(vertices,left,top,w,h,phase_x,phase_y,round_x)
                s=scores.setdefault(family+'/'+label,{'samples':0,'exact':0,'max_channel_delta':0,'failures':[]})
                for i,(count,pixel) in enumerate(zip(counts,case['pixels'])):
                    actual=[v*count//16 for v in (144,120,8,255)]
                    s['samples']+=1;s['exact']+=actual==pixel;s['max_channel_delta']=max(s['max_channel_delta'],max(abs(a-b) for a,b in zip(actual,pixel)))
                    if actual!=pixel:s['failures'].append({'case':int(k[1]),'kind':int(k[2]),'x':left+i%w,'y':top+i//w,'coverage_count':count,'actual':actual,'native':pixel})
    return {'scores':scores,'routing':'one vertex/scan construction globally; no native RGB input',
            'coverage_admitted':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyze(a.native);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for k,v in r['scores'].items():print(k,v['exact'],v['samples'],v['max_channel_delta'])
