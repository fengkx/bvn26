"""Reject coefficient-domain chroma expansion against controls and original JPEG3."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.build_jpeg_controls import controls
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_jpeg_color_sequences import rgb
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_original_jpeg import analyze as original_check


def compare(jpeg,target,alpha,subsampling,executable,output):
    output.mkdir(parents=True,exist_ok=True)
    path=output/'input.jpg';path.write_bytes(jpeg)
    width,height=Image.open(BytesIO(jpeg)).size
    for scale in ((1,2) if subsampling==2 else (1,)):
        folder=output/f'scale{scale}';folder.mkdir(exist_ok=True)
        p=subprocess.run([str(executable),str(path),str(folder),str(scale)],capture_output=True,check=True)
        (folder/'decode.log').write_bytes(p.stderr)
    plane_paths=[output/'scale1/c0.pgm']+[output/f"scale{2 if subsampling==2 else 1}/c{c}.pgm" for c in (1,2)]
    planes=[Image.open(p) for p in plane_paths]
    assert all(p.size==(width,height) and p.mode=='L' for p in planes)
    values=list(zip(*(p.getdata() for p in planes)));assert len(values)==len(target)==width*height
    failures=[]
    for i,(v,expected) in enumerate(zip(values,target)):
        actual=rgb(v,'floor-contributions')+[alpha[i]] if alpha[i] else [0]*4
        if actual!=expected:failures.append({'x':i%width,'y':i//width,'ycbcr':v,'candidate':actual,'native':expected,'delta':[a-b for a,b in zip(actual,expected)]})
    return {'pixels':len(target),'exact':len(target)-len(failures),
            'max_channel_delta':max((max(map(abs,f['delta'])) for f in failures),default=0),
            'plane_sha256':[hashlib.sha256(p.read_bytes()).hexdigest() for p in plane_paths],'failures':failures}


def analyze(executable,output):
    native=ROOT/'evidence/importer-loud-fail/r212/native';generated=controls()
    assert json.loads((native/'build.json').read_text())['cases']==[c for c,_ in generated]
    targets=[]
    for kind,data in events(native):
        if kind=='case':targets.append([])
        elif kind=='row':targets[-1].extend([[(v>>s)&255 for s in (16,8,0,24)] for v in map(int,data.split(',')[1:])])
    rows=[]
    for (case,jpeg),target in zip(generated,targets):
        if case['mode']!='RGB':continue
        result=compare(jpeg,target,[255]*len(target),case['subsampling'],executable,output/f"control{case['id']}")
        rows.append({'case':case,**result})
    native=ROOT/'evidence/importer-loud-fail/r210/native';original_check(native)
    # Retain the source table/image seam normalization already verified in r211.
    from tools.probes.build_bound_bitmap_component import source_tags
    import struct,zlib
    payload=next(p for c,p,_ in source_tags(ROOT/'game/fighter/orochimaru.swf') if c==35 and struct.unpack_from('<H',p)[0]==340)
    length=struct.unpack_from('<I',payload,2)[0];jpeg=payload[6:6+length];alpha=zlib.decompress(payload[6+length:])
    assert jpeg.count(b'\xff\xd9\xff\xd8')==1
    seam=jpeg.index(b'\xff\xd9\xff\xd8');assert seam==572 and seam<jpeg.index(b'\xff\xc0')
    joined=jpeg[:seam]+jpeg[seam+4:]
    target=[]
    for kind,data in events(native)[1:-1]:
        assert kind=='row';target.extend(unpack(list(map(int,data.split(',')))[1:]))
    assert [p[3] for p in target]==list(alpha) and set(alpha)=={0,255}
    original=compare(joined,target,alpha,2,executable,output/'original')
    result={'controls':rows,'control_pixels':sum(r['pixels'] for r in rows),'control_exact':sum(r['exact'] for r in rows),
            'original':original,'dump_executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
            'production_admitted':False}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dump',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=analyze(args.dump,args.output)
    print('controls',r['control_exact'],r['control_pixels']);print('original',r['original']['exact'],r['original']['pixels'],r['original']['max_channel_delta'])
