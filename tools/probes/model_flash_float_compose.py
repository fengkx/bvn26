"""Instruction-derived bounded float compose; MXCSR and source routing remain hypotheses."""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from tools.probes.extract_cache_affine_binary import BINARY_SHA256

START, END = 0x10029dc2d, 0x10029ddad


def f32(value):
    if value != 0 and abs(value) < 2**-126:
        raise ValueError('Subnormal/underflow input is outside the bounded MXCSR hypothesis')
    value = struct.unpack('<f',struct.pack('<f',float(value)))[0]
    if not math.isfinite(value) or (value != 0 and abs(value) < 2**-126):
        raise ValueError('Nonfinite/subnormal arithmetic is outside the bounded MXCSR hypothesis')
    return value


def bits(value):
    return struct.unpack('<I',struct.pack('<f',value))[0]


def i32(value):
    return (value+2**31) % 2**32-2**31


def cvtss2si_rtne(value):
    if not math.isfinite(value) or not -2**31 <= round(value) < 2**31:
        raise ValueError('SSE invalid integer conversion is outside this bounded model')
    return round(value)


def as_float(matrix):
    if matrix['flags'] not in (0,1) or len(matrix['linear']) != 4 or len(matrix['translation']) != 2:
        raise ValueError('Only independently described fixed0/float1 matrices are modeled')
    translation = list(matrix['translation'])
    if any(type(v) is not int or not -2**31 <= v < 2**31 for v in translation):
        raise ValueError('Translation fields must be signed int32')
    if matrix['flags'] == 0:
        if any(type(v) is not int or not -2**31 <= v < 2**31 for v in matrix['linear']):
            raise ValueError('Fixed coefficients must be signed int32')
        linear = [f32(f32(v)*2**-16) for v in matrix['linear']]
    else:
        linear = [f32(v) for v in matrix['linear']]
    return {'linear':linear,'translation':translation,'flags':1}


def compose_float(child, parent):
    """Model RSI(parent) after RDI(child), with RTNE an explicit unverified MXCSR choice."""
    if not (child['flags'] == 1 or parent['flags'] == 1):
        raise ValueError('Both fixed inputs route to a different native branch')
    left,right = as_float(child),as_float(parent)
    a,b,c,d = left['linear']; e,f,g,h = right['linear']
    tx,ty = map(f32,left['translation']); px,py = right['translation']
    multiply=lambda x,y:f32(x*y)
    add=lambda x,y:f32(x+y)
    axis = (bits(b)|bits(c)|bits(f)|bits(g)) == 0
    if axis:
        linear=[multiply(a,e),0.0,0.0,multiply(h,d)]
        x,y = multiply(e,tx),multiply(h,ty)
    else:
        # Packed instruction lanes add the second column product to the first.
        linear=[add(multiply(g,b),multiply(e,a)),add(multiply(h,b),multiply(f,a)),
                add(multiply(g,d),multiply(e,c)),add(multiply(h,d),multiply(f,c))]
        x=add(multiply(e,tx),multiply(g,ty))
        y=add(multiply(f,tx),multiply(h,ty))
    return {'linear':linear,'translation':[i32(cvtss2si_rtne(x)+px),i32(cvtss2si_rtne(y)+py)],'flags':1}


def authored_twips(value):
    twips=Fraction(str(value))*20
    if twips.denominator != 1:
        raise ValueError('Authored display translation is not exactly on the twip grid')
    return int(twips)


def scene_matrix(spec, shape):
    """One globally declared twip→quarter hierarchy hypothesis, not native ownership proof."""
    draw=list(map(Fraction,spec['draw']))
    seed=f32(f32(4)*f32(.05))
    current={'linear':[f32(f32(v)*seed) for v in draw[:4]],
             'translation':[math.trunc(v*4) for v in draw[4:]],'flags':1}
    stages=[{'stage':'draw_quarter_from_twips','matrix':current}]
    for name in ('outer','matrix'):
        source=list(map(Fraction,spec[name]))
        child={'linear':[f32(v) for v in source[:4]],
               'translation':[authored_twips(v) for v in spec[name][4:]],'flags':1}
        current=compose_float(child,current)
        stages.append({'stage':name,'input':child,'matrix':current})
    fill=spec.get('fill_matrix',shape['bitmap_matrix'])
    exact_fill=[Fraction(round(Fraction(fill.get(k,d))*65536),65536*20) for k,d in
                (('scaleX','1'),('rotateSkew0','0'),('rotateSkew1','0'),('scaleY','1'))]
    exact_fill += [Fraction(int(fill.get(k,'0')),20) for k in ('translateX','translateY')]
    display=[Fraction(v)*5 for v in current['linear']]+[Fraction(v,4) for v in current['translation']]
    from tools.probes.analyze_jinye_smooth_leaf import compose
    matrix=compose(display,exact_fill)
    stages.append({'stage':'retained_exact_authored_fill','matrix':[str(v) for v in exact_fill]})
    return matrix,{'stages':stages,'mxcsr_rtne_observed':False,'hierarchy_and_fill_routing_proved':False,
                   'device_seed_field_four_proved':False,'draw_translation_rule':'retained trunc(drawtranslation*4), not constructor proof',
                   'units':'display inputs twips; draw maps twips to quarter pixels; display linear *20/4 and translation /4 then unchanged exact authored fill',
                   'production_admitted':False}



def pin(binary, disassembly):
    data=binary.read_bytes()
    if hashlib.sha256(data).hexdigest()!=BINARY_SHA256:raise ValueError('Unpinned executable')
    segments=[];position=32
    for _ in range(struct.unpack_from('<I',data,16)[0]):
        command,size=struct.unpack_from('<II',data,position)
        if command==0x19:
            _,_,_,address,_,offset,length=struct.unpack_from('<II16sQQQQ',data,position)
            segments.append((address,offset,length))
        position+=size
    def raw(address,length):
        offsets=[o+address-a for a,o,n in segments if a<=address and address+length<=a+n]
        if len(offsets)!=1:raise ValueError('Ambiguous binary range')
        return data[offsets[0]:offsets[0]+length]
    lines=[];cursor=START
    for line in disassembly.open():
        match=re.match(r'([0-9a-f]+):\s+([0-9a-f ]+)\s+(.+)$',line)
        if not match:continue
        address=int(match[1],16)
        if address<START:continue
        if address>=END:break
        code=bytes.fromhex(match[2])
        if address!=cursor or code!=raw(address,len(code)):raise ValueError('Instruction bytes/gaps differ')
        cursor+=len(code);lines.append(line.rstrip())
    if cursor!=END:raise ValueError('Incomplete float branch')
    constants={hex(a):raw(a,n).hex() for a,n in ((0x10107ba10,16),(0x101079878,4),(0x10107ba48,4))}
    if struct.unpack('<4f',bytes.fromhex(constants['0x10107ba10']))!=(2**-16,)*4:raise ValueError('Conversion vector differs')
    if struct.unpack('<f',bytes.fromhex(constants['0x101079878']))!=(2**-16,):raise ValueError('Conversion scalar differs')
    if struct.unpack('<f',bytes.fromhex(constants['0x10107ba48']))!=(f32(.05),):raise ValueError('Device scalar differs')
    device_start,device_end=0x10015c991,0x10015c9ca
    device_lines=[];device_cursor=device_start
    for line in disassembly.open():
        match=re.match(r'([0-9a-f]+):\s+([0-9a-f ]+)\s+(.+)$',line)
        if not match:continue
        address=int(match[1],16)
        if address<device_start:continue
        if address>=device_end:break
        code=bytes.fromhex(match[2])
        if address!=device_cursor or code!=raw(address,len(code)):raise ValueError('Device constructor bytes differ')
        device_cursor+=len(code);device_lines.append(line.rstrip())
    if device_cursor!=device_end:raise ValueError('Incomplete device constructor')
    return {'binary_sha256':BINARY_SHA256,'span':[hex(START),hex(END)],'bytes_hex':raw(START,END-START).hex(),
            'instructions':lines,'device_constructor':{'span':[hex(device_start),hex(device_end)],'bytes_hex':raw(device_start,device_end-device_start).hex(),'instructions':device_lines},'constants':constants,'rounding_mode_observed':False,
            'source_fill_routing_proved':False,'production_admitted':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=Path,required=True)
    p.add_argument('--disassembly',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=pin(a.binary,a.disassembly);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
