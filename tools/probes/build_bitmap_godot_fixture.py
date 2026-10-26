#!/usr/bin/env python3
"""Build Godot sampler inputs from pinned native traces, never CPU predictions."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.probes.analyze_bitmap_phase import analyze as phase_capture
from tools.probes.analyze_bitmap_inverse import analyze as inverse
from tools.probes.analyze_bitmap_repeat_rounding import capture as spans
from tools.probes.analyze_bitmap_repeat_spans import capture as long_spans
from tools.probes.analyze_bitmap_sampling_r27 import rgb, ROOT


def rgba_capture(text):
    identities=[(v,r,s,start,length) for v in range(2) for r in range(2)
                for s in (3,5,8,1.7) for start in (3,4) for length in (1,4,8,260)]
    events=[line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    if (len(events)!=len(identities)+1 or any(len(e)!=8 for e in events)
        or len({e[1] for e in events})!=1 or not events[0][1].startswith('filter-bitmap-transparent-rgba-r32-')
        or [int(e[2]) for e in events]!=list(range(len(events))) or events[-1][6:]!=['done','ok']):
        raise ValueError('Invalid RGBA capture sequence/completion')
    rows=[]
    for identity,e in zip(identities,events):
        values=list(map(float,e[7].split(',')))
        if e[6]!='rgba' or tuple(values[:5])!=identity or len(values)!=5+identity[-1]:
            raise ValueError('Invalid RGBA capture identity/count')
        if any(v!=int(v) or not -0x80000000<=v<=0xffffffff for v in values[5:]):
            raise ValueError('Invalid native ARGB word')
        rows.append((identity,[int(v) & 0xffffffff for v in values[5:]]))
    return rows


def build(root=ROOT):
    cases, hashes = [], {}
    def read(path):
        data = (root/path).read_bytes(); hashes[path] = hashlib.sha256(data).hexdigest()
        return data.decode()
    for extended, folder in [(False,'bitmap-phase'),(True,'bitmap-phase-extended')]:
        text=read(f'r22/{folder}/native.log');phase_capture(text,extended=extended)
        for line in text.splitlines():
            fields=line.split('|')
            if len(fields)!=8 or fields[6]!='phase':continue
            values=list(map(float,fields[7].split(',')));alpha,scale=values[:2]
            for p,pixel in zip(range(-256 if extended else 0,256),values[2:]):
                cases.append({'suite':folder,'repeat':False,'width':2,'height':2,
                              'sx':scale,'sy':scale,'tx':p/256,'ty':-p/512 if extended else 0,
                              'left':0,'right':32,'shape_left':0,'pattern':'basis','alpha':int(alpha),
                              'x':math.floor(scale),'y':math.floor(scale),'expected':rgb(int(pixel))+[255]})
    for kind, path in [('repeat','r23/inverse'),('clipped','r23/inverse-clipped'),
                       ('row','r23/row'),('scalar-repeat','r24/scalar-repeat'),
                       ('scalar-clipped','r24/scalar-clipped')]:
        for r in inverse(read(path+'/native.log'), kind)['rows']:
            repeat = 'repeat' in kind
            scalar = kind.startswith('scalar')
            tx, ty = r['phase']/256, -r['phase']/512
            cases.append({'suite':kind, 'repeat':repeat, 'width':2 if repeat else 1024,
                          'height':2 if repeat else 1024, 'sx':r['scale'], 'sy':r['scale'],
                          'tx':tx,'ty':ty,'x':r['x'],'y':r['y'],
                          'left':r['x'] if scalar else 0, 'right':r['x']+1 if scalar else 520,
                          'shape_left':0, 'pattern':'basis','alpha':r['alpha'],
                          'expected':r['native_rgb']+[255]})
    for ident, pixels in spans(read('r30/spans/native.log'), 'span'):
        n, corner, scale, origin, length = ident
        cases.append({'suite':'r30-spans','repeat':True,'width':n,'height':n,'sx':scale,'sy':8,
                      'tx':-origin,'ty':0,'left':4,'right':4+length,'shape_left':-4096,
                      'pattern':'unique','corner':corner,'alpha':255,'y':4,
                      'row_expected':[rgb(p)+[255] for p in pixels]})
    for kind, path in [('interval','intervals'),('chunk','chunks')]:
        for ident, pixels in long_spans(read(f'r31/{path}/native.log'),kind):
            pattern, case, start, length = ident
            cases.append({'suite':'r31-'+kind,'repeat':True,'width':2,'height':2,
                          'sx':(5,3)[case],'sy':8,'tx':-(0,-15)[case],'ty':0,
                          'left':start,'right':start+length,'shape_left':-4096,
                          'pattern':'impulse','corner':pattern,'alpha':255,'y':4,
                          'row_expected':[rgb(p)+[255] for p in pixels]})
    rgba = read('r32/rgba/native.log')
    for identity,pixels in rgba_capture(rgba):
        varying,repeat,scale,start,length=identity
        cases.append({'suite':'rgba-varying' if varying else 'rgba-constant','repeat':bool(repeat),
                      'width':2,'height':2,'sx':scale,'sy':scale,'tx':-.5,'ty':.25,
                      'left':start,'right':start+length,'shape_left':-4096,'pattern':'basis',
                      'alpha':128,'varying_alpha':bool(varying),'straight_rgba':True,'y':4,
                      'row_expected':[rgb(p&0xffffff)+[p>>24] for p in pixels]})
    return {'format' :'bitmap-native-godot-v1','cases':cases,'reference_sha256':hashes,
            'samples':sum(len(c.get('row_expected',[0])) for c in cases)}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=build();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({'samples':result['samples'],'cases':len(result['cases'])}))
