"""Diagnostic axis-aligned clipped sampler. Repeat and coverage are not admitted.

r27 independently pins inverse matrix coefficients before scan initialization.
The clipped path uses geometric runs, never native RGB, to select arithmetic.
"""
import math


def coordinates(scale, tx, ty, x, y):
    if scale <= 0:
        raise ValueError('Candidate only covers positive uniform scale')
    tx, ty = math.trunc(tx*4)/4, math.trunc(ty*4)/4
    inverse = math.floor(65536/scale+.5)
    half = math.floor(inverse/2+.5)
    return ((x*inverse + math.floor(-tx/scale*65536+.5)+half)/65536-.5,
            (y*inverse + math.floor(-ty/scale*65536+.5)+half)/65536-.5)


def use_byte_weights(scale, tx, ty, x, y, *, clip_left, clip_right,
                     source_width, source_height, shape_left=0):
    # Only full-coverage pixels are modeled. The first full pixel anchors chunks.
    tx = math.trunc(tx*4)/4
    full_left = max(clip_left, math.ceil(shape_left*scale+tx))
    if x < full_left:
        raise ValueError('Geometry coverage fringe is outside the sampler candidate')
    chunk_left = full_left + ((x-full_left)//256)*256
    chunk_end = min(clip_right, chunk_left+256)
    _, sy = coordinates(scale, tx, ty, x, y)
    if sy < 1 or sy >= source_height-1:
        return True
    start, end = chunk_left, chunk_end
    while start < end and coordinates(scale, tx, ty, start, y)[0] < 1:
        start += 1
    while end > start and coordinates(scale, tx, ty, end-1, y)[0] >= source_width-1:
        end -= 1
    return not (start <= x < start + ((end-start)//4)*4)


def interpolate(sx, sy, texel, *, byte_weights):
    ix, iy = math.floor(sx), math.floor(sy)
    fx, fy = math.floor((sx-ix)*256), math.floor((sy-iy)*256)
    colors = [texel(ix+dx, iy+dy) for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))]
    if byte_weights:
        weights = [(256-fx)*(256-fy)//256, fx*(256-fy)//256, (256-fx)*fy//256]
        weights.append(256-sum(weights))
        return [sum(w*c[k] for w, c in zip(weights, colors))//256 for k in range(3)]
    left = [(colors[0][k]*(256-fy)+colors[2][k]*fy)//256 for k in range(3)]
    right = [(colors[1][k]*(256-fy)+colors[3][k]*fy)//256 for k in range(3)]
    return [(left[k]*(256-fx)+right[k]*fx)//256 for k in range(3)]


def sample_clipped(scale, tx, ty, x, y, texel, **bounds):
    byte_weights = use_byte_weights(scale, tx, ty, x, y, **bounds)
    width, height = bounds['source_width'], bounds['source_height']
    def clamped(a, b):
        return texel(max(0, min(width-1, a)), max(0, min(height-1, b)))
    return interpolate(*coordinates(scale, tx, ty, x, y), clamped, byte_weights=byte_weights)
