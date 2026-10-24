"""Diagnostic positive-axis repeat spans; not a production rasterizer.

The r30 scalar initializer is unchanged. Span boundaries come from geometry,
256-pixel work chunks and texture periods, never observed native pixel values.
"""
import math

from tools.probes.analyze_bitmap_repeat_rounding import coordinate
from tools.probes.bitmap_sampling_candidate import interpolate


def span_modes(scale, translation, start, length, width, y, height):
    """start is the first fully covered pixel, already intersected with the clip."""
    xs = [coordinate(scale, translation, pixel, width) for pixel in range(start, start+length)]
    modes = ['byte']*length
    runs = []
    left = 0
    while left < length:
        period = math.floor(xs[left]/width)
        end = left+1
        while (end < length and end//256 == left//256
               and math.floor(xs[end]/width) == period):
            end += 1
        bulk_end = left+(end-left)//4*4
        mode = 'byte'
        if bulk_end > left:
            # Monotone positive scales make the final X footprint sufficient.
            # A wrapped neighbor changes the separable interpolation order for
            # the entire bulk batch, not just the pixel touching that neighbor.
            safe = xs[bulk_end-1] % width < width-1 and y % height < height-1
            mode = 'vertical' if safe else 'horizontal'
            modes[left:bulk_end] = [mode]*(bulk_end-left)
        runs.append({'start': start+left, 'end': start+end, 'bulk_end': start+bulk_end,
                     'period': period, 'bulk_mode': mode})
        left = end
    return xs, modes, runs


def sample(x, y, texel, mode):
    if mode in ('byte', 'vertical'):
        return interpolate(x, y, texel, byte_weights=mode == 'byte')
    if mode != 'horizontal':
        raise ValueError('Unknown repeat interpolation mode')
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = math.floor((x-ix)*256), math.floor((y-iy)*256)
    colors = [texel(ix+dx, iy+dy) for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))]
    top = [(colors[0][k]*(256-fx)+colors[1][k]*fx)//256 for k in range(3)]
    bottom = [(colors[2][k]*(256-fx)+colors[3][k]*fx)//256 for k in range(3)]
    return [(top[k]*(256-fy)+bottom[k]*fy)//256 for k in range(3)]
