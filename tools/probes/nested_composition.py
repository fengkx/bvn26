"""Explicit native byte-buffer boundaries and exact nested-layer comparisons."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from tools.probes.normal_composition import over

PALETTES = ((0x3355cc, 0x81d3ef, 0x46c4ec, 0xff8001),
            (0xffffff, 0x017ffe, 0xcc80aa, 0x7f0180))
SIZES = {'child': (8, 8), 'parent': (12, 8), 'final': (16, 8)}


def cases():
    result = []
    for palette in range(2):
        for alpha in (0, 1, 64, 128, 254, 255):
            for child in (0, 1, 25, 50, 99, 100):
                for parent in (0, 1, 25, 50, 99, 100):
                    result.append([len(result), palette, alpha, child, parent])
    return result


def rgba(color, alpha):
    return [(((color >> shift) & 255) * alpha + 127) // 255 for shift in (16, 8, 0)] + [alpha]


def inputs(case):
    _, palette, alpha, _, _ = case
    b, m, a, c = PALETTES[palette]
    return {'back': rgba(b, alpha), 'middle': rgba(m, 128),
            'leaf_a': rgba(a, 63), 'leaf_b': rgba(c, 191), 'sentinel': rgba(c, 127)}


def predicted(case):
    colors = inputs(case)
    _, _, _, child_opacity, parent_opacity = case

    def draw(target, width, pixel_at, left, top, size, opacity=100):
        multiplier = opacity*256//100
        for y in range(size[1]):
            for x in range(size[0]):
                index = (top+y)*width+left+x
                front = [c*multiplier//256 for c in pixel_at(x, y)]
                target[index] = over(target[index], front)

    child = [[0]*4 for _ in range(64)]
    draw(child, 8, lambda x,y: colors['leaf_a'], 0, 0, (8,8))
    draw(child, 8, lambda x,y: colors['leaf_b'], 2, 2, (4,4))
    parent = [[0]*4 for _ in range(96)]
    draw(parent, 12, lambda x,y: colors['middle'], 0, 0, (12,8))
    draw(parent, 12, lambda x,y: child[y*8+x], 2, 0, (8,8), child_opacity)
    final = [[0]*4 for _ in range(128)]
    draw(final, 16, lambda x,y: colors['back'], 0, 0, (16,8))
    draw(final, 16, lambda x,y: parent[y*12+x], 2, 0, (12,8), parent_opacity)
    draw(final, 16, lambda x,y: colors['sentinel'], 6, 0, (2,8))
    return {'child': child, 'parent': parent, 'final': final}


def decode(directory):
    build = json.loads((directory/'build.json').read_text())
    if hashlib.sha256(Path(build['source']).read_bytes()).hexdigest() != build['source_sha256']:
        raise ValueError('Native source hash mismatch')
    expected = []
    for case in cases():
        expected.append(('case', case))
        expected.append(('inputs', case))
        for stage in SIZES:
            expected.extend(('row', [case[0], stage, y]) for y in range(8))
    expected.append(('done', 'ok'))
    seen = 0
    rows = [{stage: [] for stage in SIZES} for _ in cases()]
    for line in (directory/'native.log').read_text().splitlines():
        p = line.split('|')
        if p[:2] != ['AIREF', build['run_id']]:
            continue
        if (len(p) != 8 or seen >= len(expected)
                or p[2:6] != [str(seen), '0', '0', '0'] or p[6] != expected[seen][0]):
            raise ValueError('Missing, reordered, duplicate or unexpected native event')
        kind, identity = expected[seen]
        if kind == 'done':
            if p[7] != identity:
                raise ValueError('Invalid completion')
        elif kind == 'case':
            if list(map(int, p[7].split(','))) != identity:
                raise ValueError('Unexpected case identity')
        elif kind == 'inputs':
            packed = list(map(int, p[7].split(',')))
            if len(packed) != 11 or packed[0] != identity[0]:
                raise ValueError('Unexpected source input count')
            for i, pixel in enumerate(inputs(identity).values()):
                straight, black = packed[1+i*2:3+i*2]
                got = [(black >> s)&255 for s in (16,8,0)] + [(straight >> 24)&255]
                if (black >> 24)&255 != 255 or got != pixel:
                    raise ValueError('Unsupported BitmapData constructor premultiplication')
        else:
            fields = p[7].split(',')
            if [int(fields[0]), fields[1], int(fields[2])] != identity:
                raise ValueError('Unexpected stage or row identity')
            index, stage, _ = identity
            width = SIZES[stage][0]
            packed = list(map(int, fields[3:]))
            if len(packed) != width*2 or any(not -2**31 <= n < 2**32 for n in packed):
                raise ValueError('Invalid pixel count or packed value')
            for i in range(0, len(packed), 2):
                straight, black = packed[i:i+2]
                if (black >> 24) & 255 != 255:
                    raise ValueError('Black readback must be opaque')
                rows[index][stage].append([(black >> s)&255 for s in (16,8,0)] + [(straight >> 24)&255])
        seen += 1
    if seen != len(expected):
        raise ValueError('Incomplete native capture')
    return rows


def compare(native, actual):
    if len(native) != len(cases()) or len(actual) != len(native):
        raise ValueError('Missing cases')
    identities = cases()
    scores = {s: {'pixels': 0, 'exact': 0, 'max_delta': 0, 'failures': []} for s in SIZES}
    for index, (reference, observed) in enumerate(zip(native, actual)):
        if set(reference) != set(SIZES) or set(observed) != set(SIZES):
            raise ValueError('Missing or unknown buffer')
        for stage, (width, height) in SIZES.items():
            if len(reference[stage]) != width*height or len(observed[stage]) != width*height:
                raise ValueError('Buffer extent mismatch')
            score = scores[stage]
            for pixel, (expected, got) in enumerate(zip(reference[stage], observed[stage])):
                if len(got) != 4 or any(not isinstance(c, int) or not 0 <= c <= 255 for c in got):
                    raise ValueError('Invalid RGBA byte')
                delta = max(abs(a-b) for a,b in zip(expected,got))
                score['pixels'] += 1
                score['exact'] += delta == 0
                score['max_delta'] = max(score['max_delta'], delta)
                if delta:
                    score['failures'].append({'case': identities[index], 'x': pixel%width, 'y': pixel//width,
                                              'expected': expected, 'actual': got})
    return {'production_admitted': False, 'passed': all(s['pixels'] == s['exact'] for s in scores.values()),
            'scores': scores}


def read_atlases(directory):
    rows = [{} for _ in cases()]
    for stage, (width, height) in SIZES.items():
        image = Image.open(directory/(stage+'.png')).convert('RGBA')
        if image.size != (width, height*len(rows)):
            raise ValueError('Unexpected atlas extent')
        pixels = [list(p) for p in image.getdata()]
        for index, row in enumerate(rows):
            row[stage] = pixels[index*width*height:(index+1)*width*height]
    return rows
