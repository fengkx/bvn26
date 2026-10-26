"""Reject fixed affine initializer reductions against retained positive-axis controls.

Only clipped coordinate initialization is substituted. Existing geometry-only
span interpolation and the independently admitted repeat initializer stay fixed.
This is a necessary reduction check, not affine smoothing admission.
"""
import argparse
from fractions import Fraction
from functools import lru_cache
import json
import math
from pathlib import Path
from unittest.mock import patch

from tools.probes.analyze_affine_rounded_footprint import prepare
from tools.probes.analyze_clipped_half_step import decode, texel
from tools.probes import bitmap_half_even_candidate as retained
from tools.probes.build_bound_bitmap_component import ROOT


@lru_cache(maxsize=None)
def axis_coefficients(scale, translation):
    scale, translation = Fraction(str(scale)), Fraction(str(translation))
    assert scale > 0
    translation = Fraction(math.trunc(translation*4),4)
    row = (1/scale,Fraction(0),-translation/scale)
    a,b,t,offset,_ = prepare((row,),'ties_even')[0]
    # Positive-axis reduction must agree for the center and norm hypotheses.
    assert b == 0 and offset == round(Fraction(a+b,2))
    return a,t,offset


def axis(scale, translation, pixel, rule):
    assert rule == 'even'
    a,t,offset = axis_coefficients(scale,translation)
    return Fraction(pixel*a+t+offset-32768,65536)


def scalar_controls():
    cases,inputs = decode(ROOT/'evidence/importer-loud-fail/r91/native')
    total=exact=0;failures=[]
    for case in cases:
        index,width,scale,origin,*_ = case['key'];width=int(width)
        for x,target in enumerate(case['pixels']):
            if x < origin or x+1 > origin+width*scale:
                continue
            coordinate=axis(scale,origin,x,'even')
            integer=math.floor(coordinate);fraction=math.floor((coordinate-integer)*256)
            left,right=[texel(max(0,min(width-1,j))) for j in (integer,integer+1)]
            actual=[(a*(256-fraction)+b*fraction)//256 for a,b in zip(left,right)]+[255]
            total+=1;exact+=actual==target
            if actual!=target:
                failures.append({'case':int(index),'x':x,'actual':actual,'native':target})
    return {'source_pixels':inputs,'samples':total,'exact':exact,'failures':failures}


def analyze():
    scalar=scalar_controls()
    with patch.object(retained,'axis',axis):
        old=retained.old_controls()
        leaf=retained.jiraiya_controls()
        spans=retained.span_controls()
    passed=(scalar['exact']==scalar['samples'] and old['exact']==old['samples']
            and leaf['exact_images']==len(leaf['cases']) and spans['exact']==spans['samples'])
    return {'construction':'positive-axis reduction shared by fixed-center and minimum-norm ties-even hypotheses',
            'scalar':scalar,'old':old,'jiraiya':leaf,'spans':spans,
            'axis_reduction_exact':passed,'repeat_initializer_changed':False,
            'affine_smoothing_admitted':False,'production_admitted':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=analyze()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(result['axis_reduction_exact'],result['scalar']['exact'],result['old']['exact'],
          result['jiraiya']['exact_images'],result['spans']['exact'])
    raise SystemExit(0 if result['axis_reduction_exact'] else 1)
