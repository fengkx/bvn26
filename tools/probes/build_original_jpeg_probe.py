"""Expose the unchanged source JPEG3 tag to native BitmapData.loadBitmap."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib
from tools.probes.build_bound_bitmap_component import ROOT, source_tags, tag
from tools.probes.build_flash_filter_probe import build


def prepare(output, ffdec):
    source = ROOT / 'game/fighter/orochimaru.swf'
    inventory = json.loads((ROOT / 'evidence/importer-loud-fail/r209/orochimaru.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == inventory['source']['sha256']
    bitmap = next(raw for code, payload, raw in source_tags(source)
                  if code == 35 and struct.unpack_from('<H', payload)[0] == 340)
    assert hashlib.sha256(bitmap).hexdigest() == inventory['raw_tag_sha256']['340']
    report = build('orochimaru-jpeg-source', output, ffdec)
    path = output / 'game/main.swf'
    raw = path.read_bytes()
    assert raw[:3] in (b'FWS', b'CWS')
    body = raw[8:] if raw[:3] == b'FWS' else zlib.decompress(raw[8:])
    start = (5 + 4 * (body[0] >> 3) + 7) // 8 + 4
    export = tag(56, struct.pack('<HH', 1, 340) + b'original_bitmap_340\0')
    body = body[:start] + bitmap + export + body[start:]
    path.write_bytes(b'FWS' + raw[3:4] + struct.pack('<I', len(body) + 8) + body)
    report.update({'original_source': inventory['source'], 'original_bitmap_tag_sha256': inventory['raw_tag_sha256']['340'],
                   'production_admitted': False})
    report['outputs_sha256']['game/main.swf'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output, args.ffdec)
