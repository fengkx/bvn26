"""Strict complete original nearest leaf GPU gate; no production binding."""
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
from tools.probes.analyze_affine_rounded_footprint import prepare
from tools.probes.analyze_affine_scan_translation import vertices, fixed_scan
from tools.probes.build_bound_bitmap_component import ROOT

NATIVE = ROOT/'evidence/importer-loud-fail/r179/native'


def fixture(output):
    output.mkdir(parents=True, exist_ok=True)
    original, source, cases = decode(NATIVE)
    leaf = original['leaf']
    assert leaf['fill']['fillStyleType'] == '67' and leaf['smooth_sampling'] is False
    assert leaf['fill_masks'] == [[[[137.0,0.0],[137.0,200.0],[0.0,200.0],[0.0,0.0]]]]
    (output/'source.rgba').write_bytes(bytes(c for p in source for c in p))
    specs = []
    for ci in range(2):
        folder = output/f'case{ci}'; folder.mkdir(exist_ok=True)
        authored = original['cases'][ci]
        key = [format(float(v), '.15g') for v in authored[:6]+[1,0,0,1]+authored[6:]]
        assert list(map(Fraction,key)) == list(map(Fraction,cases[ci]['key'][3:15]))
        fixed = prepare(tuple(inverse_signed(['0']*5+key)), 'ties_even')
        counts = fixed_scan(vertices(['0']*3+['137','200']+key),0,0,600,400,16,'trunc')
        packed = bytearray(600*400*32); coordinates = bytearray(600*400*16)
        maximum = 0; negative = 0
        for i,count in enumerate(counts):
            if not count:continue
            x,y = i%600,i//600
            for axis,(a,b,t,offset,_) in enumerate(fixed):
                stages = [a*x,b*y,a*x+b*y,a*x+b*y+t,a*x+b*y+t+offset]
                assert all(-2**31+65536 < v < 2**31-65536 for v in stages)
                maximum = max(maximum,max(abs(v) for v in stages)); negative += stages[-1]<0
                for slot,value in enumerate((a,b,t,offset)):
                    assert -2**31 <= value < 2**31
                    struct.pack_into('<i',packed,i*32+(axis*4+slot)*4,value)
            struct.pack_into('<4f',coordinates,i*16,x,y,0,count)
        (folder/'coefficients.bin').write_bytes(packed)
        (folder/'coordinates.bin').write_bytes(coordinates)
        Image.frombytes('L',(600,400),bytes(counts)).save(folder/'coverage.png')
        Image.frombytes('RGBA',(600,400),bytes(c for p in cases[ci]['pixels'] for c in p)).save(folder/'native.png')
        specs.append({'folder':folder.name,'size':[600,400],'covered_pixels':sum(bool(v) for v in counts),
                      'matrix_properties':key,'max_integer_intermediate':maximum,'negative_sample_axes':negative})
    spec={'source_size':[137,200],'source_metadata':{k:v for k,v in leaf.items() if k!='pixels_premultiplied'},
          'source_owner_sha256':original['source_owner_sha256'],'source_matrix_bytes':original['source_matrix_bytes'],
          'raw_tag_sha256':original['raw_tag_sha256'],'cases':specs,
          'scope':'complete untinted leaf; actual mask and raw texels; no wrapper filters/CXFORM', 'production_admitted':False}
    (output/'fixture.json').write_text(json.dumps(spec,indent=2)+'\n')
    return spec


def compare(output):
    spec=json.loads((output/'fixture.json').read_text());rows=[]
    for case in spec['cases']:
        folder=output/case['folder'];actual=Image.open(folder/'actual.png').convert('RGBA');native=Image.open(folder/'native.png').convert('RGBA')
        assert actual.size==native.size==(600,400)
        differences=[];maximum=0
        for i,(p,q) in enumerate(zip(actual.getdata(),native.getdata())):
            maximum=max(maximum,max(abs(a-b) for a,b in zip(p,q)))
            if p!=q:differences.append({'x':i%600,'y':i//600,'actual':list(p),'native':list(q)})
        rows.append({'case':case['folder'],'samples':240000,'exact':240000-len(differences),
                     'max_channel_delta':maximum,'failures':differences})
    return {'rows':rows,'complete_leaf_gpu_exact':all(not v['failures'] for v in rows),
            'complete_wrapper_admitted':False,'production_admitted':False,'full_production_suite_rerun':False}


def run(godot,output):
    spec=fixture(output)
    for case in spec['cases']:
        path=output/case['folder']/'actual.png'
        if path.exists():path.unlink()
    command=[str(godot),'--path',str(ROOT/'godot'),'--rendering-method','gl_compatibility','--quit-after','600','-s',str(ROOT/'godot/tests/affine_component_coverage.gd'),'--',str(output/'fixture.json'),str(output)]
    p=subprocess.run(command,capture_output=True,text=True,timeout=180);log=p.stdout+p.stderr;(output/'godot.log').write_text(log)
    if p.returncode or 'ERROR' in log or 'AFFINE_COMPONENT_COVERAGE_OK cases=2' not in log:
        raise ValueError('Incomplete full leaf GPU diagnostic: '+log)
    result=compare(output);(output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    files=['tools/probes/run_nearest_component_coverage.py','godot/tests/affine_component_coverage.gd','godot/tests/affine_component_coverage.gdshader','tools/probes/analyze_affine_scan_translation.py','tools/probes/analyze_affine_rounded_footprint.py','evidence/importer-loud-fail/r179/native/native.log.gz','evidence/importer-loud-fail/r179/native/fixture.json.gz']
    provenance={'command':command,'exit':p.returncode,'godot_sha256':sha(godot),'source_sha256':{n:sha(ROOT/n) for n in files},
                'readback_sha256':{str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file() and p.name!='provenance.json'},'production_admitted':False}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--godot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=run(a.godot.resolve(),a.output.resolve());print('exact',sum(v['exact'] for v in r['rows']),480000)
    raise SystemExit(0 if r['complete_leaf_gpu_exact'] else 1)
