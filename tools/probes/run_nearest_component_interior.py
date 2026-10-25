"""Bind original indexed texels and masks to a strictly interior GPU diagnostic."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from PIL import Image
from tools.probes.analyze_nearest_component_input import decode
from tools.probes.analyze_affine_heldout import inverse_signed
from tools.probes.analyze_affine_rounded_footprint import prepare,indices
from tools.probes.build_bound_bitmap_component import ROOT

NATIVE=ROOT/'evidence/importer-loud-fail/r179/native'


def fixture(output):
    output.mkdir(parents=True,exist_ok=True);original,source,cases=decode(NATIVE)
    assert original['leaf']['fill']['fillStyleType']=='67' and original['leaf']['smooth_sampling'] is False
    assert original['leaf']['fill_masks']==[[[[137.0,0.0],[137.0,200.0],[0.0,200.0],[0.0,0.0]]]]
    (output/'source.rgba').write_bytes(bytes(c for p in source for c in p));specs=[]
    for ci in range(2):
        folder=output/f'case{ci}';folder.mkdir(exist_ok=True)
        authored=original['cases'][ci];properties=authored[:6]+[1,0,0,1]+authored[6:]
        key=[format(float(v),'.15g') for v in properties]
        assert list(map(Fraction,key))==list(map(Fraction,cases[ci]['key'][3:15]))
        co=inverse_signed(['0']*5+key);fixed=prepare(tuple(co),'ties_even')
        packed=bytearray(600*400*32);coordinates=bytearray(600*400*16);phase=bytearray(600*400*16);mask=bytearray(600*400)
        count=0;max_intermediate=0
        for y in range(400):
            for x in range(600):
                if not all(1<=a*x+b*y+t+min(0,a)+min(0,b) and a*x+b*y+t+max(0,a)+max(0,b)<=limit-1 for (a,b,t),limit in zip(co,(137,200))):continue
                i=y*600+x;count+=1;mask[i]=255
                ix,iy=indices(co,x,y,'ties_even');assert 0<=ix<137 and 0<=iy<200
                assert source[iy*137+ix]==cases[ci]['pixels'][i]
                for axis,(a,b,t,offset,_) in enumerate(fixed):
                    intermediate=[a*x,b*y,a*x+b*y,a*x+b*y+t,a*x+b*y+t+offset]
                    assert all(-2**31<=v<2**31 for v in intermediate) and intermediate[-1]>=0
                    max_intermediate=max(max_intermediate,max(abs(v) for v in intermediate))
                    for slot,value in enumerate((a,b,t,offset)):
                        assert -2**31<=value<2**31
                        struct.pack_into('<i',packed,i*32+(axis*4+slot)*4,value)
                struct.pack_into('<4f',coordinates,i*16,x,y,0,1)
                struct.pack_into('<4f',phase,i*16,0,1,0,1)
        for name,data in [('coefficients',packed),('coordinates',coordinates),('phase',phase)]:
            (folder/(name+'.bin')).write_bytes(data)
        Image.frombytes('L',(600,400),bytes(mask)).save(folder/'proved-interior.png')
        Image.frombytes('RGBA',(600,400),bytes(c for p in cases[ci]['pixels'] for c in p)).save(folder/'native.png')
        specs.append({'folder':folder.name,'size':[600,400],'proved_interior_pixels':count,'matrix_properties':key,'max_integer_intermediate':max_intermediate})
    leaf={k:v for k,v in original['leaf'].items() if k!='pixels_premultiplied'}
    spec={'source_size':[137,200],'source_metadata':leaf,'source_owner_sha256':original['source_owner_sha256'],
          'source_matrix_bytes':original['source_matrix_bytes'],'raw_tag_sha256':original['raw_tag_sha256'],
          'cases':specs,'scope':'untinted leaf interior only; original mask retained; no filter/CXFORM consumer','production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(spec,indent=2)+'\n');return spec


def compare(output):
    spec=json.loads((output/'fixture.json').read_text());rows=[]
    for case in spec['cases']:
        folder=output/case['folder'];a=Image.open(folder/'actual.png').convert('RGBA');b=Image.open(folder/'native.png').convert('RGBA');mask=Image.open(folder/'proved-interior.png')
        assert a.size==b.size==mask.size==(600,400)
        pixels=list(a.getdata());native=list(b.getdata());selection=list(mask.getdata());assert set(selection)=={0,255}
        chosen=[i for i,v in enumerate(selection) if v];assert len(chosen)==case['proved_interior_pixels']
        failures=[{'x':i%600,'y':i//600,'actual':list(pixels[i]),'native':list(native[i])} for i in chosen if pixels[i]!=native[i]]
        rows.append({'case':case['folder'],'samples':len(chosen),'exact':len(chosen)-len(failures),'failures':failures,
                     'unproven_nonzero_native_pixels':sum(not selection[i] and p[3]!=0 for i,p in enumerate(native)),
                     'unclaimed_output_clear':all(p==(0,0,0,0) for i,p in enumerate(pixels) if not selection[i])})
    return {'rows':rows,'interior_gpu_exact':all(not v['failures'] and v['unclaimed_output_clear'] for v in rows),
            'complete_component_admitted':False,'production_admitted':False,'full_production_suite_rerun':False}


def run(godot,output):
    spec=fixture(output)
    for case in spec['cases']:
        target=output/case['folder']/'actual.png'
        if target.exists():target.unlink()
    command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s',str(ROOT/'godot/tests/affine_component_interior.gd'),'--',str(output/'fixture.json'),str(output)]
    p=subprocess.run(command,capture_output=True,text=True,timeout=180);log=p.stdout+p.stderr;(output/'godot.log').write_text(log)
    if p.returncode or 'ERROR' in log or 'AFFINE_COMPONENT_INTERIOR_OK cases=2' not in log:raise ValueError('Incomplete component GPU diagnostic: '+log)
    r=compare(output);(output/'report.json').write_text(json.dumps(r,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/run_nearest_component_interior.py','godot/tests/affine_component_interior.gd','godot/tests/affine_nearest_integer.gdshader','tools/probes/analyze_affine_rounded_footprint.py','tools/probes/analyze_nearest_component_input.py','evidence/importer-loud-fail/r179/native/native.log.gz','evidence/importer-loud-fail/r179/native/fixture.json.gz']
    provenance={'command':command,'exit':p.returncode,'godot_sha256':sha(godot),'source_sha256':{n:sha(ROOT/n) for n in files},
                'readback_sha256':{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file() and p.name!='provenance.json'},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=run(a.godot.resolve(),a.output.resolve());print('exact',sum(v['exact'] for v in r['rows']),sum(v['samples'] for v in r['rows']));raise SystemExit(0 if r['interior_gpu_exact'] else 1)
