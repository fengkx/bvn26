"""Normalize pinned affine controls without deriving arithmetic from output pixels."""
from fractions import Fraction
import math

from tools.probes.analyze_affine_scale_split import property_float32
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_nearest_affine import decode, inverse
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.run_nested_filters import unpack


ROUNDS=(158,162,163,164,165,166,168,169,171,172)


def samples(root):
    _,cases=decode(root/'r158/native')
    for case in cases:
        co=inverse(case['key'])
        for y in range(40):
            for x in range(40):
                if not all(1<=a*xx+b*yy+t<=15 for a,b,t in co for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1))):continue
                pixel=case['pixels'][y*40+x]
                assert pixel[2:]==[73,255] and all((v-8)%15==0 for v in pixel[:2])
                yield 'r158',case['key'],co,x,y,[(v-8)//15 for v in pixel[:2]],(0,0)
    for number in ROUNDS[1:]:
        for kind,payload in events(root/f'r{number}/native'):
            if kind!='sample':continue
            v=payload.split(',');pixel=unpack(list(map(int,v[-2:])))[0];assert pixel[2:]==[73,255]
            delta=[Fraction(0),Fraction(0)]
            if number<=165 or number==171:
                key=v[:17];x,y=map(int,v[19:21])
            elif number in (166,168):
                key=v[:17];axis,step=int(v[2]),int(v[3]);x,y=map(int,v[21:23])
                delta[axis]=Fraction(math.trunc(Fraction(step,64)*20),20) if number==166 else Fraction(step,64)
                if number==168:key[5:9]=[str(property_float32(c)*64) for c in v[5:9]]
            else:
                x,y=map(int,v[15:17]);delta[int(v[4])]=Fraction(int(v[5]),64)
                key=['0']*5+[str(property_float32(c)*64) for c in v[7:11]]+['0','0','1','0','0','1','128','128']
            yield f'r{number}',v[:-2],inverse_signed(key),x,y,pixel[:2],delta
