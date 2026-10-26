#!/usr/bin/env python3
"""Bind a source-backed rectangular bitmap leaf to the bounded diagnostic sampler."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import struct
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from bitmap_shape_polygon import bitmap_shape_fill_polygons
sys.path.insert(0, str(ROOT / 'tools/probes'))
from build_minimal_swf import rect, tag

SOURCE = 'game/fighter/yulong.swf'
TIMELINE = 'godot/generated/fighters/yulong/timeline.json'


def source_tags(path):
    raw = path.read_bytes()
    if raw[:3] not in (b'FWS', b'CWS'):
        raise ValueError('Unsupported SWF compression')
    body = raw[8:] if raw[:3] == b'FWS' else zlib.decompress(raw[8:])
    offset = (5 + 4 * (body[0] >> 3) + 7) // 8 + 4
    while offset < len(body):
        start = offset
        header, = struct.unpack_from('<H', body, offset)
        offset += 2
        size = header & 63
        if size == 63:
            size, = struct.unpack_from('<I', body, offset)
            offset += 4
        payload = body[offset:offset + size]
        if len(payload) != size:
            raise ValueError('Truncated source tag')
        offset += size
        yield header >> 6, payload, body[start:offset]


def validate_binding(shape, bitmap):
    fills = shape.findall('.//fillStyles/item')
    if len(fills) != 1 or fills[0].get('fillStyleType') != '65' or fills[0].get('bitmapId') != '148':
        raise ValueError('Diagnostic requires the authored single smooth clipped fill')
    m = fills[0].find('bitmapMatrix')
    if (float(m.get('scaleX', 1)) != 20 or float(m.get('scaleY', 1)) != 20
            or any(float(m.get(k, 0)) for k in ('rotateSkew0', 'rotateSkew1', 'translateX', 'translateY'))):
        raise ValueError('Fill matrix outside diagnostic domain')
    if bitmap.get('type') != 'DefineBitsLossless2Tag' or bitmap.get('bitmapFormat') != '5':
        raise ValueError('Diagnostic requires native premultiplied lossless ARGB')
    width, height = int(bitmap.get('bitmapWidth')), int(bitmap.get('bitmapHeight'))
    contours = bitmap_shape_fill_polygons(shape)
    if contours is None or len(contours) != 1 or len(contours[0]) != 1:
        raise ValueError('Uncompiled shape mask')
    polygon = contours[0][0]
    if len(polygon) != 4 or set(map(tuple, polygon)) != {(0, 0), (width, 0), (width, height), (0, height)}:
        raise ValueError('Coverage outside full rectangular diagnostic domain')
    if shape.findall('.//lineStyles/item'):
        raise ValueError('Authored strokes are not supported by this diagnostic')
    return width, height, contours


def validate_fixture(fixture):
    if fixture['production_admitted'] is not False or fixture['source'] != SOURCE:
        raise ValueError('Not a closed diagnostic source binding')
    if fixture['shape_id'] != 155 or fixture['bitmap_id'] != 148:
        raise ValueError('Unexpected source symbols')
    if hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest() != fixture['source_sha256']:
        raise ValueError('Locked source hash mismatch')
    raw = {struct.unpack_from('<H', p)[0]: (p, r) for c, p, r in source_tags(ROOT/SOURCE)
           if c in (2, 36) and struct.unpack_from('<H', p)[0] in (148, 155)}
    if {str(k): hashlib.sha256(r).hexdigest() for k, (_, r) in raw.items()} != fixture['raw_tag_sha256']:
        raise ValueError('Original tag hash mismatch')
    payload = raw[148][0]
    _, format_id, width, height = struct.unpack_from('<HBHH', payload)
    if format_id != 5 or [width, height] != [fixture['width'], fixture['height']]:
        raise ValueError('Unexpected source bitmap format/dimensions')
    argb = zlib.decompress(payload[7:])
    pixels = [list(argb[i+1:i+4])+[argb[i]] for i in range(0, len(argb), 4)]
    if pixels != fixture['pixels_premultiplied']:
        raise ValueError('Diagnostic texels differ from original premultiplied bytes')
    shape = ET.fromstring(fixture['shape_xml'])
    bitmap = ET.Element('item', type='DefineBitsLossless2Tag', bitmapFormat='5',
                        bitmapWidth=str(width), bitmapHeight=str(height))
    _, _, contours = validate_binding(shape, bitmap)
    if (fixture['fill_masks'] != contours or fixture['fill'] != dict(shape.find('.//fillStyles/item').attrib)
            or fixture['fill_matrix'] != dict(shape.find('.//bitmapMatrix').attrib)):
        raise ValueError('Diagnostic dropped or changed authored fill metadata/mask')
    if fixture['target_size'] != [288, 40] or not fixture['cases']:
        raise ValueError('Invalid diagnostic target/cases')
    for case in fixture['cases']:
        if set(case) != {'sx', 'sy', 'tx', 'ty', 'clip'}:
            raise ValueError('Unknown transform/clip fields')
        if any(not isinstance(case[k], (int, float)) or not math.isfinite(case[k]) for k in ('sx', 'sy', 'tx', 'ty')):
            raise ValueError('Nonfinite transform')
        if (case['sx'] <= 0 or case['sy'] <= 0
                or any(v != int(v) for v in (case['tx'], case['ty'], width*case['sx'], height*case['sy']))):
            raise ValueError('Unproven fractional coverage or nonpositive scale')
        clip = case['clip']
        if len(clip) != 4 or any(v != int(v) for v in clip) or min(clip[2:]) <= 0:
            raise ValueError('Unproven clip coverage')
    return fixture


def build(output, ffdec):
    output = output.resolve()
    if any(p == output or p in output.parents for p in (ROOT/'game', ROOT/'scripts')):
        raise ValueError('Cannot overwrite locked inputs')
    output.mkdir(parents=True, exist_ok=True)
    timeline = json.loads((ROOT/TIMELINE).read_text())
    digest = hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest()
    if digest != timeline['source_swf']['sha256']:
        raise ValueError('Source hash mismatch')
    xml = output/'source.xml'
    subprocess.run(['java', f'-Duser.home={output}', '-Djava.awt.headless=true', '-jar', str(ffdec), '-swf2xml', str(ROOT/SOURCE), str(xml)], check=True, stdout=subprocess.DEVNULL)
    tags = ET.parse(xml).getroot().find('tags')
    shape = next(t for t in tags if t.get('shapeId') == '155')
    bitmap = next(t for t in tags if t.get('characterID') == '148')
    width, height, contours = validate_binding(shape, bitmap)
    argb = zlib.decompress(bytes.fromhex(bitmap.get('zlibBitmapData')))
    if len(argb) != width * height * 4:
        raise ValueError('Incorrect native bitmap size')
    pixels = [list(argb[i+1:i+4])+[argb[i]] for i in range(0, len(argb), 4)]
    cases = [{'sx': s, 'sy': s, 'tx': 4, 'ty': 4, 'clip': [0, 0, 288, 40]} for s in (1, 3, 5, 8)]
    cases += [{'sx': 3, 'sy': 5, 'tx': 4, 'ty': 4, 'clip': [9, 6, 92, 10]},
              {'sx': 5, 'sy': 3, 'tx': 4, 'ty': 4, 'clip': [11, 5, 151, 6]}]
    raw_tags = {}
    for code, payload, raw in source_tags(ROOT/SOURCE):
        if code in (2, 36) and struct.unpack_from('<H', payload)[0] in (148, 155):
            raw_tags[struct.unpack_from('<H', payload)[0]] = raw
    if set(raw_tags) != {148, 155}:
        raise ValueError('Missing original shape/bitmap tags')
    fixture = {'source': SOURCE, 'source_sha256': digest, 'shape_id': 155, 'bitmap_id': 148,
               'raw_tag_sha256': {str(k): hashlib.sha256(v).hexdigest() for k, v in raw_tags.items()},
               'width': width, 'height': height, 'pixels_premultiplied': pixels,
               'shape_xml': ET.tostring(shape, encoding='unicode'), 'fill_masks': contours,
               'fill': dict(shape.find('.//fillStyles/item').attrib),
               'fill_matrix': dict(shape.find('.//bitmapMatrix').attrib),
               'cases': cases, 'target_size': [288, 40], 'production_admitted': False}
    validate_fixture(fixture)
    (output/'fixture.json').write_text(json.dumps(fixture, indent=2)+'\n')
    (output/'shape.xml').write_text(ET.tostring(shape, encoding='unicode')+'\n')
    run = 'bound-bitmap-r33-' + uuid.uuid4().hex[:12]
    script = '''stop();var seq=0;
function emit(k,v){trace("AIREF|RUN|"+(seq++)+"|0|0|0|"+k+"|"+v);}
var mc=_root.attachMovie("leaf","leaf",1);var cases=CASES;
for(var i=0;i<cases.length;i++){
 var c=cases[i];var b=new flash.display.BitmapData(288,40,true,0);
 b.draw(mc,new flash.geom.Matrix(c.sx,0,0,c.sy,c.tx,c.ty),null,null,new flash.geom.Rectangle(c.clip[0],c.clip[1],c.clip[2],c.clip[3]));
 for(var y=0;y<40;y++){var row=[];for(var x=0;x<288;x++)row.push(b.getPixel32(x,y));emit("row",i+","+y+","+row.join(","));}b.dispose();
}
emit("done","ok");fscommand("quit");
'''.replace('RUN', run).replace('CASES', re.sub(r'"([a-z_]+)":', r'\1:', json.dumps(cases)))
    (output/'scripts/frame_1').mkdir(parents=True, exist_ok=True)
    (output/'scripts/frame_1/DoAction.as').write_text(script)
    (output/'game').mkdir(exist_ok=True)
    wrapper = struct.pack('<HH', 60000, 1) + tag(26, b'\x06'+struct.pack('<HH', 1, 155)+b'\0') + tag(1) + tag(0)
    body = (rect(0, 5760, 0, 800) + struct.pack('<HH', 30*256, 1)
            + raw_tags[148] + raw_tags[155] + tag(39, wrapper)
            + tag(56, struct.pack('<HH', 1, 60000)+b'leaf\0') + tag(12, b'\0') + tag(1) + tag(0))
    (output/'base.swf').write_bytes(b'FWS'+bytes([8])+struct.pack('<I', len(body)+8)+body)
    subprocess.run(['java', f'-Duser.home={output}', '-Djava.awt.headless=true', '-jar', str(ffdec), '-importScript', str(output/'base.swf'), str(output/'game/main.swf'), str(output/'scripts')], check=True, stdout=subprocess.DEVNULL)
    compiled_tags = {struct.unpack_from('<H', p)[0]: r for c, p, r in source_tags(output/'game/main.swf')
                     if c in (2, 36) and struct.unpack_from('<H', p)[0] in (148, 155)}
    if compiled_tags != raw_tags:
        raise ValueError('Instrumentation changed the original shape or bitmap tag')
    metadata = {'run_id': run, 'source': SOURCE, 'source_sha256': digest,
                'raw_tags_preserved': True, 'ffdec_sha256': hashlib.sha256(ffdec.read_bytes()).hexdigest(),
                'fixture_sha256': hashlib.sha256((output/'fixture.json').read_bytes()).hexdigest(),
                'outputs_sha256': {'game/main.swf': hashlib.sha256((output/'game/main.swf').read_bytes()).hexdigest()}}
    (output/'build.json').write_text(json.dumps(metadata, indent=2)+'\n')
    return fixture


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    args = parser.parse_args()
    build(args.output, args.ffdec.resolve())
