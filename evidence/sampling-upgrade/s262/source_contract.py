"""Retain the authored timer/digit/HUD placement changes from a fresh SWF XML export."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SYMBOLS = (1810, 1813, 1814, 1815)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xml', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    xml = ET.parse(args.xml).getroot()
    scripts = json.loads((ROOT / 'scripts/main.json').read_text())['scripts']
    result = {'main_sha256': hashlib.sha256((ROOT / 'game/main.swf').read_bytes()).hexdigest(),
              'xml_sha256': hashlib.sha256(args.xml.read_bytes()).hexdigest(), 'symbols': {}}
    for symbol in SYMBOLS:
        sprite = next(t for t in xml.iter('item') if t.get('type') == 'DefineSpriteTag' and t.get('spriteId') == str(symbol))
        frame = 1
        changes = []
        for tag in sprite.find('subTags'):
            kind = tag.get('type')
            if kind == 'ShowFrameTag':
                frame += 1
            elif kind.startswith(('PlaceObject', 'RemoveObject')) or kind == 'FrameLabelTag':
                changes.append({'frame': frame, 'tag': ET.tostring(tag, encoding='unicode')})
        result['symbols'][str(symbol)] = {'frame_count': int(sprite.get('frameCount')), 'changes': changes,
                                         'scripts': [s for s in scripts if s['path'].startswith(f'DefineSprite_{symbol}/')]}
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print('S262_SOURCE_CONTRACT_OK symbols=' + str(len(SYMBOLS)))


if __name__ == '__main__':
    main()
