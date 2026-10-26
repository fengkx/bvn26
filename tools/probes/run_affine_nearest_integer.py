"""GPU diagnostic: common integer affine arithmetic, raw texels, no production binding."""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
from PIL import Image

from tools.probes.analyze_affine_rounded_footprint import samples as old_samples, prepare, indices
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_nearest_affine import decode
from tools.probes.run_nested_filters import unpack

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail'


def samples():
    yield from old_samples(EVIDENCE)
    for kind,payload in events(EVIDENCE/'r177/native'):
        if kind!='sample':continue
        v=payload.split(',');pixel=unpack(list(map(int,v[-2:])))[0];assert pixel[2:]==[73,255]
        x,y=map(int,v[19:21])
        yield 'r177',v[:-2],inverse_signed(v[:17]),x,y,pixel[:2],(0,0)


def fixture(output):
    output.mkdir(parents=True,exist_ok=True)
    records=list(samples());assert len(records)==68322
    width=512;height=math.ceil(len(records)/width);count=width*height
    names=('ax','bx','tx','ox','ay','by','ty','oy')
    arrays={name:bytearray(count*4) for name in names}
    arrays.update({name:bytearray(count*16) for name in ('coordinates','phase')})
    source16,_=decode(EVIDENCE/'r158/native');source128=[]
    for kind,payload in events(EVIDENCE/'r162/native'):
        if kind=='source':source128.extend(unpack(list(map(int,payload.split(',')[1:]))))
    assert source128==[[x,y,73,255] for y in range(128) for x in range(128)]
    atlas=source128+[[0,0,0,0] for _ in range(128*128)]
    for y in range(16):
        for x in range(16):atlas[(y+128)*128+x]=source16[y*16+x]
    (output/'source.rgba').write_bytes(bytes(c for p in atlas for c in p))
    expected=[];suites={};max_intermediate=0
    for i,(suite,key,co,x,y,native,delta) in enumerate(records):
        assert indices(co,x,y,'ties_even',delta)==native
        base=128 if suite=='r158' else 0
        bound=16 if suite=='r158' else 128
        assert all(0<=v<bound for v in native)
        expected.append(atlas[(native[1]+base)*128+native[0]])
        suites[suite]=suites.get(suite,0)+1
        rows=prepare(tuple(co),'ties_even');phases=[]
        for axis,((a,b,t,offset,_),d) in enumerate(zip(rows,delta)):
            d=Fraction(d);assert 0<d.denominator<=64
            # Every arithmetic stage used by the shader is checked before upload.
            intermediates=[a*x,b*y,a*x+b*y,a*x+b*y+t,a*x+b*y+t+offset]
            q=intermediates[-1]
            intermediates += [q*d.denominator,d.numerator*65536,q*d.denominator-d.numerator*65536,d.denominator*65536]
            assert all(-2**31<=v<2**31 for v in intermediates) and intermediates[-2]>=0
            max_intermediate=max(max_intermediate,max(abs(v) for v in intermediates))
            for name,value in zip(names[axis*4:axis*4+4],(a,b,t,offset)):
                assert -2**31<=value<2**31
                struct.pack_into('<i',arrays[name],i*4,value)
            phases.extend((d.numerator,d.denominator))
        struct.pack_into('<4f',arrays['coordinates'],i*16,x,y,base,1)
        struct.pack_into('<4f',arrays['phase'],i*16,*phases)
    packed = bytearray(count * 32)
    for i in range(count):
        for slot,name in enumerate(names):packed[i*32+slot*4:i*32+slot*4+4] = arrays[name][i*4:i*4+4]
    (output/'coefficients.bin').write_bytes(packed)
    for name in ('coordinates','phase'):(output/(name+'.bin')).write_bytes(arrays[name])
    padded=expected+[[0,0,0,0] for _ in range(count-len(expected))]
    Image.frombytes('RGBA',(width,height),bytes(c for p in padded for c in p)).save(output/'expected.png')
    spec={'samples':len(records),'size':[width,height],'suites':suites,'max_integer_intermediate':max_intermediate,
          'raw_source_texels':16384+256,'scope':'opaque nearest interior, scalar control positions only','production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(spec,indent=2)+'\n')
    return spec


def compare(output):
    spec=json.loads((output/'fixture.json').read_text());actual=Image.open(output/'actual.png').convert('RGBA');expected=Image.open(output/'expected.png').convert('RGBA')
    assert actual.size==expected.size==tuple(spec['size'])
    a=list(actual.getdata());b=list(expected.getdata());rows=[];start=0
    for suite,count in spec['suites'].items():
        aa=a[start:start+count];bb=b[start:start+count]
        rows.append({'suite':suite,'samples':count,'exact':sum(p==q for p,q in zip(aa,bb)),
                     'max_channel_delta':max(abs(v-w) for p,q in zip(aa,bb) for v,w in zip(p,q))})
        start+=count
    failures=[{'index':i,'actual':list(p),'native':list(q)} for i,(p,q) in enumerate(zip(a[:start],b[:start])) if p!=q]
    return {'samples':start,'exact':start-len(failures),'suites':rows,'failures':failures,
            'padding_exact':a[start:]==b[start:],'bounded_gpu_exact':not failures and a[start:]==b[start:],
            'production_admitted':False,'full_production_suite_rerun':False}


def run(godot,output):
    spec=fixture(output)
    target=output/'actual.png'
    if target.exists():target.unlink()
    command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s',str(ROOT/'godot/tests/affine_nearest_integer.gd'),'--',str(output/'fixture.json'),str(output)]
    p=subprocess.run(command,capture_output=True,text=True,timeout=180);log=p.stdout+p.stderr;(output/'godot.log').write_text(log)
    if p.returncode or 'ERROR' in log or f"AFFINE_NEAREST_INTEGER_OK samples={spec['samples']}" not in log:raise ValueError('Incomplete GPU diagnostic: '+log)
    r=compare(output);(output/'report.json').write_text(json.dumps(r,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/run_affine_nearest_integer.py','tools/probes/analyze_affine_rounded_footprint.py','tools/probes/affine_control_samples.py','godot/tests/affine_nearest_integer.gd','godot/tests/affine_nearest_integer.gdshader','tools/probes/analyze_affine_footprint.py','tools/probes/analyze_affine_heldout.py','tools/probes/analyze_affine_scale_split.py']
    provenance={'command':command,'exit':p.returncode,'godot_sha256':sha(godot),'source_sha256':{n:sha(ROOT/n) for n in files},
                'reference_sha256':{f'evidence/importer-loud-fail/r{n}/native/native.log.gz':sha(EVIDENCE/f'r{n}/native/native.log.gz') for n in (158,162,163,164,165,166,168,169,171,172,174,175,177)},
                'readback_sha256':{p.name:sha(p) for p in output.iterdir() if p.is_file() and p.name!='provenance.json'},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=run(a.godot.resolve(),a.output.resolve());print('exact',r['exact'],r['samples']);raise SystemExit(0 if r['bounded_gpu_exact'] else 1)
