# /// script
# dependencies = ["pillow==12.3.0"]
# ///
"""Bake source portrait timelines at their selected labels for native rendering."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from extract_timeline_geometry import extract_frames, file_sha256

ROOT = Path(__file__).resolve().parents[2]


def freeze(sprite, frame):
    children = sprite.find('subTags')
    kept = []
    current = 1
    for tag in children:
        if tag.get('type') == 'ShowFrameTag':
            if current == frame:
                break
            current += 1
        elif tag.get('type') not in ('DoActionTag', 'FrameLabelTag'):
            kept.append(copy.deepcopy(tag))
    children.clear()
    children.extend(kept)
    children.append(ET.Element('item', {'type': 'ShowFrameTag'}))
    sprite.set('frameCount', '1')


def build(workspace, temporary, output, jar, names):
    temporary.mkdir(parents=True, exist_ok=True)
    report = json.loads((workspace / 'export-report.json').read_text())
    assert report['source']['sha256'] == file_sha256(ROOT / 'game/main.swf')
    xml = workspace / 'main.xml'
    assert next(f['sha256'] for f in report['files'] if f['path'] == 'main.xml') == file_sha256(xml)
    labels = {label: f['frame'] for f in extract_frames(xml, 1346)['frames'] for label in f['labels']}
    output.mkdir(parents=True, exist_ok=True)
    link = temporary / 'main_assets'
    if not link.exists(): link.symlink_to((workspace / 'main_assets').resolve(), target_is_directory=True)
    result = {}
    for index, name in enumerate(names):
        tree = ET.parse(xml)
        sprite = next(t for t in tree.getroot().find('tags') if t.get('spriteId') == '1346')
        freeze(sprite, labels[name])
        derived = temporary / f'portrait-{index}.xml'
        tree.write(derived, encoding='utf-8', xml_declaration=True)
        swf = derived.with_suffix('.swf')
        java = ['java', '-Djava.awt.headless=true']
        subprocess.run(java + ['-jar', str(jar), '-xml2swf', str(derived), str(swf)], check=True, stdout=subprocess.DEVNULL)
        bounds = json.loads(subprocess.check_output(java + ['-cp', str(jar), str(ROOT / 'tools/importer/SpriteBounds.java'), str(swf), '1348'], text=True))
        raster = temporary / f'raster-{index}'
        subprocess.run(java + ['-jar', str(jar), '-selectid', '1348', '-export', 'sprite', str(raster), str(swf)], check=True, stdout=subprocess.DEVNULL)
        textures = []
        for frame in range(1, 6):
            texture = f'portrait-{index}-{frame}.png'
            shutil.copyfile(raster / f'DefineSprite_1348/{frame}.png', output / texture)
            textures.append(texture)
        result[name] = {'textures': textures, 'bounds_twips': bounds, 'raster_border': 5, 'source_label_frame': labels[name]}
    tree = ET.parse(xml)
    tags = tree.getroot().find('tags')
    template = next(t for t in tags if t.get('characterID') == '670')
    catalog = json.loads((ROOT / 'manifest.json').read_text())['fighter_catalog']
    footer = {}
    footer_names = list(dict.fromkeys(names + ['魂', '我爱罗']))
    ids = []
    for index, name in enumerate(footer_names):
        sid, tid = 8000 + index * 2, 8001 + index * 2
        text = copy.deepcopy(template)
        text.set('characterID', str(tid))
        text.set('hasText', 'true')
        text.set('initialText', catalog[name]['name'])
        sprite = ET.Element('item', {'type': 'DefineSpriteTag', 'spriteId': str(sid), 'frameCount': '1'})
        children = ET.SubElement(sprite, 'subTags')
        ET.SubElement(children, 'item', {'type': 'PlaceObject2Tag', 'depth': '1', 'characterId': str(tid),
                                       'placeFlagHasCharacter': 'true', 'placeFlagMove': 'false'})
        ET.SubElement(children, 'item', {'type': 'ShowFrameTag'})
        tags.extend([text, sprite])
        ids.append(sid)
        footer[name] = {'texture': f'footer-name-{index}.png', 'text': catalog[name]['name']}
    derived = temporary / 'footer.xml'
    tree.write(derived, encoding='utf-8', xml_declaration=True)
    swf = derived.with_suffix('.swf')
    subprocess.run(java + ['-jar', str(jar), '-xml2swf', str(derived), str(swf)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(java + ['-jar', str(jar), '-zoom', '2', '-selectid', ','.join(map(str, ids)), '-export', 'sprite', str(temporary / 'footer-raster'), str(swf)], check=True, stdout=subprocess.DEVNULL)
    from PIL import Image
    for index, name in enumerate(footer_names):
        with Image.open(temporary / f'footer-raster/DefineSprite_{ids[index]}/1.png') as image:
            image.crop(image.getbbox()).save(output / footer[name]['texture'])
    (output / 'footer.json').write_text(json.dumps(footer, ensure_ascii=False, indent=2) + '\n')
    (output / 'portraits.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--temporary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('names', nargs='+')
    args = parser.parse_args()
    build(args.workspace, args.temporary, args.output, args.ffdec, args.names)
