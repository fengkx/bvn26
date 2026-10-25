"""Validate cyclic start vertices without changing the authored mask stored in the fixture."""
import math
from tools.probes.bound_bitmap_candidate import render_leaf


def canonical_rect_mask(fixture):
    matrix=fixture['fill_matrix'];x=float(matrix['translateX'])/20;y=float(matrix['translateY'])/20
    width,height=fixture['width'],fixture['height']
    if not all(math.isfinite(v) for v in (x,y,width,height)) or width<=0 or height<=0:
        raise ValueError('Invalid rectangle extent')
    corners=[[x,y],[x+width,y],[x+width,y+height],[x,y+height]]
    masks=fixture['fill_masks']
    if len(masks)!=1 or len(masks[0])!=1 or len(masks[0][0])!=4:
        raise ValueError('Only one four-edge rectangular contour is proven')
    polygon=masks[0][0]
    if not any(polygon==corners[start:]+corners[:start] for start in range(4)):
        raise ValueError('Mask does not preserve the proven rectangle winding and edges')
    return [[corners]]


def render_rect(fixture,case,target_size):
    # A cyclic start vertex changes neither the ordered edges nor their coverage.
    # Normalize only the renderer's validated view; preserve original source metadata.
    canonical=canonical_rect_mask(fixture)
    return render_leaf({**fixture,'fill_masks':canonical},case,target_size)
