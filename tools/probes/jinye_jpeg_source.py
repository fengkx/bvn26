"""Bounded source-only JPEG55 decoding, with native readback used only for comparison."""
import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import subprocess
import zlib
from PIL import Image, JpegImagePlugin
from tools.probes.build_bound_bitmap_component import ROOT, source_tags, tag
from tools.probes.build_flash_filter_probe import build
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.analyze_jpeg_row_partitions import routed_rgb
from tools.probes.run_nested_filters import unpack


def source():
    cases = json.loads((ROOT/'evidence/importer-loud-fail/r32/components/jinye/cases.json').read_text())
    identity = cases[0]['source']
    path = ROOT/identity['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == identity['sha256']
    payload, raw = next((p,r) for c,p,r in source_tags(path) if c == 35 and struct.unpack_from('<H',p)[0] == 55)
    assert hashlib.sha256(raw).hexdigest() == 'd2d1414e1435389556a5fa41a2bfb8af8472d0be3b8522991aabeb058acb18d4'
    length = struct.unpack_from('<I',payload,2)[0]
    jpeg, alpha = payload[6:6+length], zlib.decompress(payload[6+length:])
    image = Image.open(BytesIO(jpeg))
    assert image.size == (92,40) and JpegImagePlugin.get_sampling(image) == 2
    assert len(alpha) == 3680 and Counter(alpha) == {0:3531,255:149}
    assert b'\xff\xd9\xff\xd8' not in jpeg
    metadata = {'source':identity,'bitmap_id':55,'tag_sha256':hashlib.sha256(raw).hexdigest(),
                'jpeg_sha256':hashlib.sha256(jpeg).hexdigest(),'alpha_sha256':hashlib.sha256(alpha).hexdigest(),
                'width':92,'height':40,'subsampling':2,'alpha_histogram':dict(Counter(alpha))}
    return metadata, raw, jpeg, alpha


def prepare(output, ffdec):
    metadata, bitmap, _, _ = source()
    report = build('jinye-jpeg-source',output,ffdec)
    path = output/'game/main.swf'; raw = path.read_bytes()
    assert raw[:3] in (b'FWS',b'CWS')
    body = raw[8:] if raw[:3] == b'FWS' else zlib.decompress(raw[8:])
    start = (5+4*(body[0]>>3)+7)//8+4
    export = tag(56,struct.pack('<HH',1,55)+b'original_bitmap_55\0')
    body = body[:start]+bitmap+export+body[start:]
    path.write_bytes(b'FWS'+raw[3:4]+struct.pack('<I',len(body)+8)+body)
    report.update({'bitmap':metadata,'production_admitted':False})
    report['outputs_sha256']['game/main.swf'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def decoded_planes(output, alpha):
    assert len(alpha) == 3680
    paths = [output/'scale1/c0.pgm',output/'scale2/c1.pgm',output/'scale2/c2.pgm']
    planes = []
    for path in paths:
        with Image.open(path) as image:
            assert image.size == (92,40) and image.mode == 'L'
            planes.append(list(image.getdata()))
    pixels = [routed_rgb(v,i%92,92,8)+[255] if alpha[i] else [0]*4
              for i,v in enumerate(zip(*planes))]
    assert len(pixels) == 3680
    return pixels, [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]


def decode(dump, output):
    metadata, _, jpeg, alpha = source()
    output.mkdir(parents=True,exist_ok=True)
    path = output/'source.jpg'; path.write_bytes(jpeg)
    for scale in (1,2):
        folder = output/f'scale{scale}'; folder.mkdir(exist_ok=True)
        result = subprocess.run([str(dump),str(path),str(folder),str(scale)],capture_output=True,check=True)
        (folder/'decode.log').write_bytes(result.stderr)
    pixels, metadata['plane_sha256'] = decoded_planes(output,alpha)
    return metadata, pixels


def compare(native, metadata, pixels):
    build_metadata = json.loads((native/'build.json').read_text())['bitmap']
    assert build_metadata == json.loads(json.dumps(source()[0]))
    assert {k:v for k,v in json.loads(json.dumps(metadata)).items() if k != 'plane_sha256'} == build_metadata
    captured = events(native)
    assert len(captured) == 42 and captured[0] == ['dimensions','92,40,true'] and captured[-1] == ['done','ok']
    target = []
    for y,(kind,data) in enumerate(captured[1:-1]):
        values = list(map(int,data.split(',')))
        assert kind == 'row' and values[0] == y and len(values) == 185
        target.extend(unpack(values[1:]))
    assert len(target) == len(pixels) == 3680
    assert [p[3] for p in target] == list(source()[3])
    failures = [{'x':i%92,'y':i//92,'candidate':a,'native':b,'delta':[x-y for x,y in zip(a,b)]}
                for i,(a,b) in enumerate(zip(pixels,target)) if a != b]
    report = {'bitmap':metadata,'pixels':3680,'exact':3680-len(failures),'failures':failures,
              'max_channel_delta':max((max(map(abs,f['delta'])) for f in failures),default=0),
              'decoder_parity_proved':not failures,'production_admitted':False}
    return report


def analyze(native, dump, output):
    metadata, pixels = decode(dump,output)
    report = compare(native,metadata,pixels)
    (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('build','analyze'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ffdec',type=Path)
    parser.add_argument('--native',type=Path)
    parser.add_argument('--dump',type=Path)
    args = parser.parse_args()
    if args.operation == 'build':
        assert args.ffdec is not None
        prepare(args.output,args.ffdec)
    else:
        assert args.native is not None and args.dump is not None
        result = analyze(args.native,args.dump,args.output)
        print(result['exact'],result['pixels'])
        raise SystemExit(0 if result['decoder_parity_proved'] else 1)
