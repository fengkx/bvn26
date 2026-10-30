"""Audit exported s263/s266 timelines, including XML encoding-width changes."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from tools.sampling_native import sha


def audit(before, after):
    original = ET.parse(before).getroot().find('tags')
    final = ET.parse(after).getroot().find('tags')
    added = [n for n in final if n.get('spriteId') in ('60000', '60001') or n.get('name') in ('s266Retain', 's266Remove')]
    assert len(added) == 4
    child, parent, retain, remove = added
    assert child.get('spriteId') == '60000' and child.get('frameCount') == '1'
    assert parent.get('spriteId') == '60001' and parent.get('frameCount') == '3'
    tags = list(parent.find('subTags'))
    assert [n.get('type') for n in tags] == ['PlaceObject2Tag', 'DoActionTag', 'ShowFrameTag', 'ShowFrameTag', 'RemoveObject2Tag', 'ShowFrameTag']
    assert tags[0].get('characterId') == '60000' and tags[0].get('depth') == '1'
    assert tags[0].get('placeFlagMove') == 'false' and tags[0].get('name') == 'child'
    assert tags[1].get('actionBytes') == '0700' and tags[4].get('depth') == '1'
    for node, depth, name in ((retain, '30000', 's266Retain'), (remove, '30001', 's266Remove')):
        assert node.get('characterId') == '60001' and node.get('depth') == depth and node.get('name') == name
        assert node.get('placeFlagMove') == 'false'
    remaining = [n for n in final if n not in added]
    assert len(original) == len(remaining)
    differences = []

    def compare(a, b, path, root_action=False):
        assert a.tag == b.tag and len(a) == len(b)
        assert a.attrib.keys() == b.attrib.keys()
        for key in a.attrib:
            if a.get(key) == b.get(key):
                continue
            differences.append(dict(path=path, type=a.get('type'), attribute=key, before=a.get(key) if key != 'actionBytes' else 's263 action bytes', after=b.get(key) if key != 'actionBytes' else 's266 action bytes'))
            if root_action and key == 'actionBytes':
                continue
            assert key in ('moveBits', 'nScaleBits', 'numFillBits', 'nbits') and (a.get(key), b.get(key)) == ('1', '0'), differences[-1]
        for i, (left, right) in enumerate(zip(a, b)):
            compare(left, right, f'{path}/{i}')

    frame = 1
    for i, (a, b) in enumerate(zip(original, remaining)):
        compare(a, b, f'root/{i}', a.get('type') == 'DoActionTag' and frame in (1, 10))
        if a.get('type') == 'ShowFrameTag':
            frame += 1
    actions = [r for r in differences if r['attribute'] == 'actionBytes']
    assert len(actions) == 2
    return dict(original_root_tags=len(original), added_root_tags=4,
                worker_definition='DefineSprite_60000/frame_1/DoAction.as',
                retained_parent_frame=2, removing_parent_frame=3, authored_child_depth=1,
                native_child_depth=-16383, changes=differences,
                limit='XML roundtrip also canonicalizes recorded encoding widths 1 to 0; all other original attributes, actions and tag order match. Not pixel parity.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--swf', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.before, args.after)
    report['main_sha256'] = sha(args.swf)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('S266_TIMELINE_AUDIT_OK')
