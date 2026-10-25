"""Retain the exact source encoding that prevents admission of the lossless-only binding."""
import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zlib
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT, source_tags
from tools.probes.extract_rect_control_graph import extract


def inventory(xml):
    cases_path = ROOT/'evidence/importer-loud-fail/r32/components/orochimaru/cases.json'
    cases = json.loads(cases_path.read_text())
    assert len(cases) == 5 and all(c['symbol'] == 342 for c in cases)
    source = ROOT/cases[0]['source']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == cases[0]['source']['sha256']
    location = 'game/fighter/orochimaru.swf:DefineShape_341/bitmap_340: unproven image encoding tag35'
    try:
        extract(xml, cases_path, cases[0]['id'])
    except ValueError as error:
        assert str(error) == location
    else:
        raise AssertionError('Lossless-only binding unexpectedly admitted JPEG3')
    tags = ET.parse(xml).getroot().find('tags')
    wrapper = next(t for t in tags if t.get('spriteId') == '342')
    shape = next(t for t in tags if t.get('shapeId') == '341')
    raw = {struct.unpack_from('<H',p)[0]: (code,p,data) for code,p,data in source_tags(source) if code in (2,35,39)}
    code, payload, tag = raw[340]
    assert code == 35
    length = struct.unpack_from('<I',payload,2)[0]
    jpeg = payload[6:6+length]
    alpha = zlib.decompress(payload[6+length:])
    image = Image.open(BytesIO(jpeg))
    assert image.size == (186,378) and image.mode == 'RGB' and len(alpha) == 186*378
    return {'source':cases[0]['source'], 'cases':cases,
            'wrapper_xml':ET.tostring(wrapper,encoding='unicode'), 'shape_xml':ET.tostring(shape,encoding='unicode'),
            'raw_tag_sha256':{str(i):hashlib.sha256(raw[i][2]).hexdigest() for i in (340,341,342)},
            'bitmap':{'id':340,'tag':35,'width':186,'height':378,'jpeg_bytes':len(jpeg),
                      'jpeg_sha256':hashlib.sha256(jpeg).hexdigest(),'alpha_bytes':len(alpha),
                      'alpha_sha256':hashlib.sha256(alpha).hexdigest(),'alpha_histogram':dict(sorted(Counter(alpha).items()))},
            'existing_guard_error':location,'decoder_parity_proved':False,'production_admitted':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=inventory(args.xml)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(result['existing_guard_error'])
