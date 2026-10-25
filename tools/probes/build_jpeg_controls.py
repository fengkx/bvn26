"""Encode independent grayscale/color JPEG controls before any native decoding."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import zlib
from PIL import Image, features
from tools.probes.build_bound_bitmap_component import tag
from tools.probes.build_flash_filter_probe import build


def controls():
    rows = []
    for pattern in ('gray-ramp','gray-impulse','constant','chroma-edge','rgb-ramp'):
        mode = 'L' if pattern.startswith('gray') else 'RGB'
        image = Image.new(mode,(32,32))
        pixels = []
        for y in range(32):
            for x in range(32):
                if pattern == 'gray-ramp': value = (x*7+y*13)%256
                elif pattern == 'gray-impulse': value = 255 if x%8==3 and y%8==3 else 0
                elif pattern == 'constant': value = (73,127,211)
                elif pattern == 'chroma-edge': value = (232,31,80) if x<15 else (21,201,171)
                else: value = ((x*7+y*3)%256,(x*11+y*13)%256,(x*17+y*5)%256)
                pixels.append(value)
        image.putdata(pixels)
        for subsampling in ((0,) if mode == 'L' else (0,2)):
            for quality in (75,100):
                data = BytesIO();image.save(data,format='JPEG',quality=quality,subsampling=subsampling,optimize=False)
                jpeg = data.getvalue()
                rows.append(({'id':len(rows),'pattern':pattern,'mode':mode,'subsampling':subsampling,
                              'quality':quality,'input_sha256':hashlib.sha256(image.tobytes()).hexdigest(),
                              'jpeg_sha256':hashlib.sha256(jpeg).hexdigest()},jpeg))
    assert len(rows)==16
    return rows


def prepare(output,ffdec):
    report = build('jpeg-decoder-controls',output,ffdec)
    cases = controls();tags = b'';exports = struct.pack('<H',len(cases))
    (output/'encoded').mkdir(exist_ok=True)
    for case,jpeg in cases:
        bitmap_id = case['id']+1
        tags += tag(21,struct.pack('<H',bitmap_id)+jpeg)
        exports += struct.pack('<H',bitmap_id)+f"jpeg_control_{case['id']}".encode()+b'\0'
        (output/'encoded'/f"{case['id']}.jpg").write_bytes(jpeg)
    path=output/'game/main.swf';raw=path.read_bytes();body=raw[8:] if raw[:3]==b'FWS' else zlib.decompress(raw[8:])
    start=(5+4*(body[0]>>3)+7)//8+4
    body=body[:start]+tags+tag(56,exports)+body[start:]
    path.write_bytes(b'FWS'+raw[3:4]+struct.pack('<I',len(body)+8)+body)
    report.update({'cases':[c for c,_ in cases],'encoder':{'Pillow':Image.__version__,'libjpeg_turbo':features.version('libjpeg_turbo')},'production_admitted':False})
    report['outputs_sha256']['game/main.swf']=hashlib.sha256(path.read_bytes()).hexdigest()
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ffdec',type=Path,required=True)
    args=parser.parse_args();prepare(args.output,args.ffdec)
