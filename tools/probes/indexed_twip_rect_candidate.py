"""Bounded indexed format3 diagnostic; retain the fractional-coverage rejection."""
import math
from fractions import Fraction
from tools.probes.bitmap_half_even_candidate import row,interpolate
from tools.probes.analyze_clipped_half_step import axis


def render_leaf(fixture,case,target_size):
    sw,sh=fixture['width'],fixture['height'];width,height=target_size
    matrix=fixture['fill_matrix'];fx,fy=float(matrix['translateX'])/20,float(matrix['translateY'])/20
    assert int(fixture['fill']['fillStyleType'])==65
    assert float(matrix['scaleX'])==float(matrix['scaleY'])==20
    assert not any(float(matrix.get(k,0)) for k in ('rotateSkew0','rotateSkew1'))
    assert fixture['fill_masks']==[[[[fx,fy],[fx+sw,fy],[fx+sw,fy+sh],[fx,fy+sh]]]]
    assert fixture['indexed_storage_verified'] is True
    assert case['sx']>0 and case['sy']>0
    raw=fixture['pixels_premultiplied']
    def texel(x,y):return raw[max(0,min(sh-1,y))*sw+max(0,min(sw-1,x))]
    assert case['sx']==case['sy']==1
    assert case['tx']*4==int(case['tx']*4) and case['ty']*4==int(case['ty']*4)
    left=case['tx']+fx*case['sx'];right=case['tx']+(fx+sw)*case['sx']
    top=case['ty']+fy*case['sy'];bottom=case['ty']+(fy+sh)*case['sy']
    # The independent twip-grid controls constrain non-tie quarter-grid edges.
    exact_left=Fraction(case['tx'])+Fraction(int(matrix['translateX']),20)
    exact_top=Fraction(case['ty'])+Fraction(int(matrix['translateY']),20)
    edges=[exact_left,exact_left+sw,exact_top,exact_top+sh]
    assert all((v*4)%1!=Fraction(1,2) for v in edges), 'Unproven coverage midpoint'
    left,right,top,bottom=[round(v*4)/4 for v in edges]
    output=[[0]*4 for _ in range(width*height)]
    for y in range(max(0,math.floor(top)),min(height,math.ceil(bottom))):
        spec={**case,'width':sw,'height':sh,'repeat':False,'fill_x':fx,'fill_y':fy,'shape_left':fx,
              'left':max(0,math.ceil(left)),'right':min(width,math.floor(right)),'y':y}
        start,xs,yy,modes=row(spec)
        for x in range(max(0,math.floor(left)),min(width,math.ceil(right))):
            xx=xs[x-start] if start<=x<start+len(xs) else axis(case['sx'],case['tx'],x,'even')-fx
            # Indexed storage uses one byte-weight rule across the entire span.
            mode='byte'
            area=max(0,min(x+1,right)-max(x,left))*max(0,min(y+1,bottom)-max(y,top))
            output[y*width+x]=[math.floor(v*area) for v in interpolate(xx,yy,texel,mode)]
    return output
