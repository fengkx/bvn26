"""Bounded CPU CXFORM hypothesis; reciprocal measurements are not ISA evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from tools.probes.analyze_materialized_controls import events, fixed_cx
from tools.probes.nested_composition import rgba
from tools.probes.normal_composition import over
from tools.probes.run_nested_filters import cases, decode, unpack


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def load_reciprocals(path):
    rows = [line.split() for line in path.read_text().splitlines()]
    if [int(row[0]) for row in rows] != list(range(1, 256)):
        raise ValueError('Incomplete or reordered independent reciprocal measurements')
    return {int(a): struct.unpack('<f', struct.pack('<I', int(bits, 16)))[0]
            for a, bits in rows}


def long_cx(pixel, opacity, reciprocals, estimated=True):
    alpha = pixel[3]
    if not alpha:
        return [0]*4
    reciprocal = reciprocals[alpha] if estimated else f32(1/alpha)
    result = []
    for channel, multiplier, offset in zip(pixel[:3], (.5, .75, 1), (8, 0, -4)):
        straight = f32(channel * reciprocal)
        transformed = f32(f32(straight * multiplier) + f32(offset/255))
        premult = f32(max(0, min(1, transformed)) * alpha)
        result.append(int(f32(premult * f32(opacity/100))))
    return result + [alpha*(opacity*256//100)//256]


def row_cx(pixel, opacity, width, x, reciprocals, estimated=True):
    if not 0 <= x < width:
        raise ValueError('Sample outside clipped row')
    # Geometry-only hypothesis, tested against independent clip translations.
    if width >= 16 and x < width//4*4:
        return long_cx(pixel, opacity, reciprocals, estimated)
    return fixed_cx(pixel, opacity)


def score(pairs):
    failures = []
    total = 0
    maximum = [0]*4
    for key, actual, native in pairs:
        total += 1
        delta = [abs(a-b) for a, b in zip(actual, native)]
        maximum = [max(a,b) for a,b in zip(maximum, delta)]
        if actual != native:
            failures.append({'key': key, 'actual': actual, 'native': native})
    return {'pixels': total, 'exact': total-len(failures),
            'max_channel_delta': maximum, 'failures': failures}


def analyze(root, previous):
    reciprocals = load_reciprocals(root/'reciprocal.txt')
    identities = []
    for pattern in (0,1):
        for alpha in (7,135,231):
            for opacity in (25,50,100):
                for width in (15,16,17,19,20):
                    for start in (4,5,7):
                        for translation in (-3,0,1):
                            identities.append([len(identities),pattern,alpha,opacity,width,start,translation])
    rows = events(root/'native', 'row', identities)
    scores = {}
    for estimated in (True,False):
        pairs = []
        for row in rows:
            index,pattern,alpha,opacity,width,start,translation = row[:7]
            if len(row) != 7+32*4:
                raise ValueError('Unexpected row payload')
            for x in range(32):
                source,native = unpack(row[7+x*4:11+x*4])
                sx = x-translation
                green = 192+sx%16 if pattern == 0 else (197 if sx%8==3 else 196)
                expected = rgba((70<<16)+(green<<8)+236, alpha) if 0<=sx<48 else [0]*4
                if source != expected:
                    raise ValueError('Source bytes changed')
                actual = row_cx(source,opacity,width,x-start,reciprocals,estimated) if start<=x<start+width else [0]*4
                pairs.append(([index,x],actual,native))
        scores['rows' if estimated else 'exact_reciprocal_negative_control'] = score(pairs)
    identities = []
    for color in range(4):
        for alpha in range(256):
            for opacity in (25,50,100):
                identities.append([len(identities),color,alpha,opacity])
    dense = events(previous/'dense','cx',identities)
    scores['scalar'] = score((row[:4],fixed_cx(unpack(row[4:])[0],row[3]),unpack(row[4:])[1]) for row in dense)
    identities = []
    for width in (1,3,4,7,8,12,15,16,17,18,31,32,33):
        for origin in (0,1,3):
            for alpha in (7,93,135,231):
                for opacity in (25,50,100):
                    identities.append([len(identities),width,origin,alpha,opacity])
    for name in ('spans','varied'):
        pairs = []
        for row in events(previous/name,'span',identities):
            index,width,origin,alpha,opacity = row[:5]
            if len(row) != 7+(width+origin+2)*2:
                raise ValueError('Unexpected held-out extent')
            for x,native in enumerate(unpack(row[7:])):
                source = rgba(0xff8001 if name=='varied' and (x-origin)%2 else 0x46c4ec,alpha)
                actual = row_cx(source,opacity,width,x-origin,reciprocals) if origin<=x<origin+width else [0]*4
                pairs.append(([index,x],actual,native))
        scores[name] = score(pairs)
    # Consume pinned native filter outputs: this isolates CXFORM/composition and
    # cannot establish GPU filter correctness or production admission.
    refs = decode(previous/'native')
    pairs = []
    for spec,ref in zip(cases(),refs):
        index,profile,alpha,child_op,parent_op,cx = spec['key']
        for stage,size,source_stage,source_size,left,top,opacity in (
                ('parent_input',18,'child_filter',12,3,3,child_op),
                ('final',24,'parent_filter',18,1,1,parent_op)):
            for y in range(size):
                for x in range(size):
                    if stage == 'parent_input':
                        actual = spec['inputs']['middle'] if 1<=x<17 and 1<=y<17 else [0]*4
                    else:
                        actual = spec['inputs']['back']
                    sx,sy = x-left,y-top
                    if 0<=sx<source_size and 0<=sy<source_size:
                        source = ref[source_stage][sy*source_size+sx]
                        front = row_cx(source,opacity,source_size,sx,reciprocals) if cx else [c*(opacity*256//100)//256 for c in source]
                        actual = over(actual,front)
                    if stage == 'final' and 10<=x<12:
                        actual = over(actual,spec['inputs']['sentinel'])
                    pairs.append(([index,stage,x,y],actual,ref[stage][y*size+x]))
    scores['native_buffer_boundaries'] = score(pairs)
    positive = {k:v for k,v in scores.items() if k!='exact_reciprocal_negative_control'}
    passed = all(v['exact']==v['pixels'] for v in positive.values())
    rejected = scores['exact_reciprocal_negative_control']['exact'] < scores['exact_reciprocal_negative_control']['pixels']
    return {'cpu_hypothesis_passed':passed and rejected,'production_admitted':False,
            'scope':'Bounded CPU model only; no instruction-set inference, GPU change or production admission.',
            'reciprocal_sha256':hashlib.sha256((root/'reciprocal.txt').read_bytes()).hexdigest(), 'scores':scores}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--previous',type=Path,default=Path('evidence/importer-loud-fail/r38'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = analyze(args.root,args.previous)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:{a:b for a,b in v.items() if a!='failures'} for k,v in result['scores'].items()}))
    raise SystemExit(0 if result['cpu_hypothesis_passed'] else 1)
