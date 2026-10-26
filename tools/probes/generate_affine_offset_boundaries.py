"""Choose arithmetic disagreements from matrix properties before native RGB capture."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_footprint import floor_surd
from tools.probes.analyze_bitmap_cache_support_local import events

TEMPLATE=Path(__file__).parent/'flash_filters/bitmap-affine-offset-boundaries.as.in'


def select(native):
    matrices={}
    for kind,payload in events(native):
        if kind=='sample':
            # Only transform properties enter selection; output RGB is never read.
            v=payload.split(',')[:17]
            matrices.setdefault(tuple(v[1:2]+v[4:17]),v)
    selected=[]
    for key in matrices.values():
        co=inverse_signed(key)
        for axis,row in enumerate(co):
            a,b,t=[math.floor(v*65536+Fraction(1,2)) for v in row]
            negative=min(0,a,b);square=Fraction(a*a+b*b,4)
            floor_offset=floor_surd(Fraction(negative),square)
            rounded_offset=floor_surd(Fraction(negative)+Fraction(1,2),square)
            if floor_offset==rounded_offset:continue
            divisor=math.gcd(b,65536);period=65536//divisor
            inverse=pow(b//divisor,-1,period)
            for x in range(768):
                rhs=(65535-floor_offset-t-a*x)%65536
                if rhs%divisor:continue
                first=(rhs//divisor*inverse)%period
                for y in range(first,768,period):
                    if all(2<=aa*xx+bb*yy+tt<=126 for aa,bb,tt in co for xx,yy in ((x-1,y-1),(x+2,y-1),(x-1,y+2),(x+2,y+2))):
                        selected.append({'key':key,'axis':axis,'x':x,'y':y,'offset_floor':floor_offset,'offset_round':rounded_offset})
    return selected


def generate(selected):
    rows=[v['key'][5:11]+v['key'][15:17]+[str(v['x']),str(v['y'])] for v in selected]
    return TEMPLATE.read_text().replace('__CASES__','['+','.join('['+','.join(row)+']' for row in rows)+']')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--selection',type=Path,required=True);a=p.parse_args()
    r=select(a.native);a.output.write_text(generate(r));a.selection.write_text(json.dumps(r,indent=2)+'\n');print('selected disagreements',len(r))
