"""Byte-domain static candidate using prior independent hardware measurements."""
from bisect import bisect_right
from functools import lru_cache
import gzip
import hashlib
import json

from tools.probes.analyze_cxform_intervals import f32, float_bits, from_bits
from tools.probes.analyze_cxform_reciprocal_image import decode
from tools.probes.analyze_cxform_scaled_image import decode as decode_scaled
from tools.probes.analyze_cxform_signed_bounds import EVIDENCE
from tools.probes.cxform_signed_bounds import validate
from tools.probes.analyze_materialized_controls import fixed_cx


@lru_cache(maxsize=1)
def construction():
    manifest = json.loads((EVIDENCE/'r58/static-binary.json').read_text())
    constants = {k:from_bits(v['bits']) for k,v in manifest['constants'].items()}
    raw = gzip.decompress((EVIDENCE/'r56/hardware.txt.gz').read_bytes())
    env = json.loads((EVIDENCE/'r56/environment.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=env['output_sha256']:
        raise ValueError('Hardware output image changed')
    runs = decode(raw.decode())
    scaled_raw = gzip.decompress((EVIDENCE/'r57/hardware-0.txt.gz').read_bytes())
    scaled_env = json.loads((EVIDENCE/'r57/environment.json').read_text())
    if hashlib.sha256(scaled_raw).hexdigest()!=scaled_env['output_sha256']['0']:
        raise ValueError('Post-scaled hardware image changed')
    scaled = decode_scaled(scaled_raw.decode(),0)
    starts,scaled_starts = [v[0] for v in runs],[v[0] for v in scaled]
    reciprocals,witnesses = {},{}
    for alpha in range(1,256):
        denominator = f32(f32(alpha*constants['normalizer'])+constants['denominator_bias'])
        bits = float_bits(denominator)
        if bits<=runs[-1][1]:
            row = runs[bisect_right(starts,bits)-1]
            if not row[0]<=bits<=row[1]:
                raise ValueError('Unmeasured reciprocal input')
            output_bits = row[2]
            kind = 'r56_raw'
        else:
            row = scaled[bisect_right(scaled_starts,bits)-1]
            if not row[0]<=bits<=row[1]:
                raise ValueError('Unmeasured post-scaled input')
            # Recover a raw measured output only when inversion is unique. This
            # uses hardware runs, never any native pixel or feasibility interval.
            output_bits = float_bits(f32(from_bits(row[2])/255))
            if (float_bits(f32(from_bits(output_bits)*255))!=row[2] or
                any(float_bits(f32(from_bits(output_bits+d)*255))==row[2] for d in (-1,1))):
                raise ValueError('Ambiguous inverse of measured output scaling')
            kind = 'r57_unique_inverse'
        reciprocals[alpha] = from_bits(output_bits)
        witnesses[alpha] = {'denominator_bits':bits,'reciprocal_bits':output_bits,'hardware_run':row,'source':kind}
    return constants,reciprocals,witnesses


@lru_cache(maxsize=200000)
def channel(args):
    validate(args)
    c,a,m,d,op = args
    if a not in range(1,256) or not 0<=c<=255:
        raise ValueError('Candidate outside byte-domain coverage')
    constants,reciprocals,_ = construction()
    value = f32(f32(f32(c*reciprocals[a])*f32(m*constants['multiplier_scale']))+d)
    value = max(0,min(constants['maximum'],value))
    output_alpha = f32(a*f32((op*256//100)*constants['multiplier_scale']))
    return int(f32(value*f32(output_alpha*constants['normalizer'])))


def pixel(source, opacity):
    a = source[3]
    if not a:
        return [0]*4
    return [channel((c,a,m,d,opacity)) for c,m,d in zip(source[:3],(128,192,256),(8,0,-4))]+[a*(opacity*256//100)//256]


def bounded(source, opacity, width, x):
    if not 0<=x<width:
        raise ValueError('Outside clipped span')
    return pixel(source,opacity) if width>=16 and x<width//4*4 else fixed_cx(source,opacity)
