"""Compare documented whole-image JPEG decoder modes without pixel-selected routing."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import subprocess
import zlib
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT, source_tags
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack
from tools.probes.analyze_original_jpeg import analyze


def compare(native, executable, output):
    baseline = analyze(native)
    source = ROOT / baseline['source']['path']
    payload = next(p for c,p,_ in source_tags(source)
                   if c == 35 and struct.unpack_from('<H',p)[0] == 340)
    length = struct.unpack_from('<I',payload,2)[0]
    jpeg = payload[6:6+length]
    alpha = zlib.decompress(payload[6+length:])
    target = []
    for kind,data in events(native)[1:-1]:
        assert kind == 'row'
        target.extend(unpack(list(map(int,data.split(',')))[1:]))
    output.mkdir(parents=True,exist_ok=True)
    (output/'original.jpg').write_bytes(jpeg)
    # The source stores table and image streams with one EOI/SOI seam.
    # djpeg stops at the first EOI; remove only that pre-image seam.
    assert jpeg.count(b'\xff\xd9\xff\xd8') == 1
    seam = jpeg.index(b'\xff\xd9\xff\xd8')
    assert seam < jpeg.index(b'\xff\xc0') < jpeg.index(b'\xff\xda')
    normalized = jpeg[:seam] + jpeg[seam+4:]
    assert Image.open(BytesIO(normalized)).convert('RGB').tobytes() == Image.open(BytesIO(jpeg)).convert('RGB').tobytes()
    path = output/'joined.jpg';path.write_bytes(normalized)
    modes = []
    for dct in ('int','fast','float'):
        for smooth in (True,False):
            name = dct + ('-smooth' if smooth else '-nosmooth')
            command = [str(executable),'-strict','-verbose','-rgb','-dct',dct]
            if not smooth:
                command.append('-nosmooth')
            process = subprocess.run(command+[str(path)],check=True,capture_output=True)
            (output/f'{name}.log').write_bytes(process.stderr)
            image = Image.open(BytesIO(process.stdout)).convert('RGB')
            assert image.size == (186,378)
            failures = []
            for i,(rgb,a,expected) in enumerate(zip(image.getdata(),alpha,target)):
                actual = list(rgb)+[255] if a else [0]*4
                if actual != expected:
                    failures.append({'x':i%186,'y':i//186,'candidate':actual,'native':expected,
                                     'delta':[x-y for x,y in zip(actual,expected)]})
            (output/f'{name}.json').write_text(json.dumps(failures,separators=(',',':'))+'\n')
            modes.append({'name':name,'command':command,'pixels':len(target),'exact':len(target)-len(failures),
                          'max_channel_delta':max((max(map(abs,r['delta'])) for r in failures),default=0),
                          'decoded_rgb_sha256':hashlib.sha256(image.tobytes()).hexdigest(),
                          'differences_sha256':hashlib.sha256((output/f'{name}.json').read_bytes()).hexdigest()})
    result = {'source':baseline['source'],'jpeg_sha256':baseline['jpeg_sha256'],
              'removed_pre_image_eoi_soi_offset':seam, 'joined_sha256':hashlib.sha256(normalized).hexdigest(),
              'decoder_executable_sha256':hashlib.sha256(executable.resolve().read_bytes()).hexdigest(),
              'version':subprocess.run([str(executable),'-version'],capture_output=True,text=True,check=True).stderr.strip(),
              'modes':modes,'production_admitted':False}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--djpeg',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(compare(args.native,args.djpeg,args.output),indent=2))
