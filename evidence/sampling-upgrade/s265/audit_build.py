"""Report every XML round-trip delta without treating serialization as parity."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def audit(before, after):
    changes = []
    def visit(a, b, path):
        if a.tag != b.tag:
            raise ValueError('changed XML structure: ' + path)
        for key in sorted(a.attrib.keys() | b.attrib.keys()):
            left, right = a.get(key), b.get(key)
            if left == right:
                continue
            kind = 'unclassified'
            if key in ('numFillBits', 'moveBits', 'nScaleBits', 'nbits') and (left, right) == ('1', '0'):
                kind = 'serialized_bit_width'
            elif key == 'actionBytes' and (path == 'swf/tags[1]/item[547]' or 'sprite1810/' in path):
                kind = 'observer_script'
                left, right = hashlib.sha256(bytes.fromhex(left)).hexdigest(), hashlib.sha256(bytes.fromhex(right)).hexdigest()
            elif key == 'placeFlagHasClipActions' and 'sprite1813/' in path and a.get('name') == '个':
                kind = 'ones_lifecycle_hook'
            changes.append(dict(path=path, attribute=key, before=left, after=right, classification=kind))
        if len(a) != len(b):
            allowed = a.get('name') == '个' and 'sprite1813/' in path and len(b) == len(a) + 1 and b[-1].tag == 'clipActions'
            changes.append(dict(path=path, before_children=len(a), after_children=len(b), classification='ones_lifecycle_records' if allowed else 'unclassified'))
            if allowed:
                records = b[-1].find('clipActionRecords')
                if len(records) != 2 or any(r.get('actionBytes') in ('', '00', None) for r in records):
                    raise ValueError('uncompiled lifecycle records')
        for i, (left, right) in enumerate(zip(a, b)):
            suffix = 'sprite' + left.get('spriteId') if left.get('spriteId') else ''
            visit(left, right, path + '/' + left.tag + '[' + str(i) + ']' + suffix)
    visit(ET.parse(before).getroot(), ET.parse(after).getroot(), 'swf')
    if any(c['classification'] == 'unclassified' for c in changes):
        raise ValueError('unclassified build differences: ' + json.dumps(changes))
    return dict(before_xml_sha256=hashlib.sha256(Path(before).read_bytes()).hexdigest(),
                after_xml_sha256=hashlib.sha256(Path(after).read_bytes()).hexdigest(), changes=changes,
                claim='All XML attribute/child-count deltas enumerated; not raster or allocation parity.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', required=True, type=Path)
    parser.add_argument('--after', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.before, args.after)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print('S265_BUILD_AUDIT_OK deltas=' + str(len(result['changes'])))
