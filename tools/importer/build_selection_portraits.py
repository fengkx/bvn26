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

from build_character_selection import selection_display_name
from extract_timeline_geometry import extract_frames, file_sha256

ROOT = Path(__file__).resolve().parents[2]


def room_crop(path):
    from PIL import Image

    with Image.open(path) as image:
        left, top, right, bottom = image.convert("RGBA").getchannel("A").getbbox()
    return [left, top, right - left, bottom - top]


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


def displayed_character_ids(sprite, frame):
    """Return the symbols present in the frozen sprite frame."""
    display_list = {}
    current_frame = 1
    for tag in sprite.find('subTags'):
        tag_type = tag.get('type')
        if tag_type == 'ShowFrameTag':
            if current_frame == frame:
                break
            current_frame += 1
        elif tag_type in ('PlaceObject2Tag', 'PlaceObject3Tag'):
            depth = tag.get('depth')
            character_id = tag.get('characterId')
            if depth is not None and character_id is not None:
                display_list[depth] = character_id
        elif tag_type == 'RemoveObject2Tag':
            display_list.pop(tag.get('depth'), None)
    return set(display_list.values())


def jpeg3_ids_for_symbols(tags, character_ids):
    """Resolve shape bitmap fills back to JPEG3 image definitions."""
    definitions = {}
    for tag in tags:
        if not tag.get('type', '').startswith('Define'):
            continue
        for key in ('characterID', 'characterId', 'shapeId', 'spriteId'):
            if tag.get(key) is not None:
                definitions[tag.get(key)] = tag
    pending = list(character_ids)
    visited = set()
    image_ids = set()
    while pending:
        character_id = pending.pop()
        if character_id in visited:
            continue
        visited.add(character_id)
        definition = definitions.get(character_id)
        if definition is None:
            continue
        if definition.get('type') == 'DefineBitsJPEG3Tag':
            image_ids.add(character_id)
            continue
        for item in definition.iter('item'):
            bitmap_id = item.get('bitmapId')
            if bitmap_id is not None:
                pending.append(bitmap_id)
            nested_id = item.get('characterId')
            if nested_id is not None:
                pending.append(nested_id)
    return image_ids


def build_jpeg3_rgba_imports(workspace, temporary, image_ids, tags, scope, java, jar, source_hashes):
    """Make RGBA replacements because FFDec's XML round-trip drops JPEG3 alpha."""
    if not image_ids:
        return None

    definitions = {tag.get('characterID'): tag for tag in tags
                   if tag.get('type') == 'DefineBitsJPEG3Tag'}
    output = temporary / f'jpeg3-rgba-import-{scope}'
    output.mkdir(parents=True, exist_ok=True)
    for image_id in sorted(image_ids, key=int):
        definition = definitions[image_id]
        source_rgb = workspace / definition.get('_externalFile')
        source_alpha = source_rgb.with_name(source_rgb.stem + '.alpha.png')
        if not source_rgb.is_file() or not source_alpha.is_file():
            raise FileNotFoundError(f'Missing JPEG3 image/alpha pair for {image_id}')
        for source_path in (source_rgb, source_alpha):
            relative_path = source_path.relative_to(workspace).as_posix()
            expected_hash = source_hashes.get(relative_path)
            if expected_hash is None or file_sha256(source_path) != expected_hash:
                raise ValueError(f'JPEG3 source asset hash mismatch: {relative_path}')
        subprocess.run(
            java + [
                '-cp', str(jar), str(ROOT / 'tools/importer/MergeJpeg3Alpha.java'),
                str(source_rgb), str(source_alpha), str(output / f'{image_id}.png'),
            ],
            check=True,
        )
    return output


def build(workspace, temporary, output, jar, names, raster_scale=2, portraits_only=False):
    temporary.mkdir(parents=True, exist_ok=True)
    report = json.loads((workspace / 'export-report.json').read_text())
    assert report['source']['sha256'] == file_sha256(ROOT / 'game/main.swf')
    source_hashes = {entry['path']: entry['sha256'] for entry in report['files']}
    xml = workspace / 'main.xml'
    assert next(f['sha256'] for f in report['files'] if f['path'] == 'main.xml') == file_sha256(xml)
    labels = {label: f['frame'] for f in extract_frames(xml, 1346)['frames'] for label in f['labels']}
    output.mkdir(parents=True, exist_ok=True)
    link = temporary / 'main_assets'
    if not link.exists(): link.symlink_to((workspace / 'main_assets').resolve(), target_is_directory=True)
    result = {}
    for index, name in enumerate(names):
        tree = ET.parse(xml)
        tags = tree.getroot().find('tags')
        sprite = next(t for t in tags if t.get('spriteId') == '1346')
        source_images = jpeg3_ids_for_symbols(
            tags,
            displayed_character_ids(sprite, labels[name]),
        )
        java = ['java', '-Djava.awt.headless=true']
        rgba_imports = build_jpeg3_rgba_imports(
            workspace, temporary, source_images, tags, index, java, jar, source_hashes
        )
        freeze(sprite, labels[name])
        derived = temporary / f'portrait-{index}.xml'
        tree.write(derived, encoding='utf-8', xml_declaration=True)
        swf = derived.with_suffix('.swf')
        subprocess.run(java + ['-jar', str(jar), '-xml2swf', str(derived), str(swf)], check=True, stdout=subprocess.DEVNULL)
        if rgba_imports is not None:
            with_alpha = temporary / f'portrait-{index}-with-alpha.swf'
            subprocess.run(java + ['-jar', str(jar), '-importImages', str(swf), str(with_alpha), str(rgba_imports)], check=True, stdout=subprocess.DEVNULL)
            swf = with_alpha
        bounds = json.loads(subprocess.check_output(java + ['-cp', str(jar), str(ROOT / 'tools/importer/SpriteBounds.java'), str(swf), '1348'], text=True))
        raster = temporary / f'raster-{index}'
        subprocess.run(java + ['-jar', str(jar), '-zoom', str(raster_scale),
                               '-selectid', '1348', '-export', 'sprite', str(raster), str(swf)],
                       check=True, stdout=subprocess.DEVNULL)
        textures = []
        for frame in range(1, 6):
            texture = f'portrait-{index}-{frame}.png'
            shutil.copyfile(raster / f'DefineSprite_1348/{frame}.png', output / texture)
            textures.append(texture)
        result[name] = {
            'textures': textures,
            'room_crop': room_crop(output / textures[-1]),
            'bounds_twips': bounds,
            'raster_border': 5,
            'raster_scale': raster_scale,
            'source_label_frame': labels[name],
        }
    (output / 'portraits.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if portraits_only:
        return

    catalog = json.loads((ROOT / 'manifest.json').read_text())['fighter_catalog']
    footer_names = list(dict.fromkeys(names + ['魂', '我爱罗', '鼬', '松本']))
    footer = {name: {'texture': f'footer-name-{index}.png', 'text': selection_display_name(catalog, name)}
              for index, name in enumerate(footer_names)}
    render_footer(xml, temporary, output, jar, footer)
    (output / 'footer.json').write_text(json.dumps(footer, ensure_ascii=False, indent=2) + '\n')


def render_footer(xml, temporary, output, jar, footer):
    java = ['java', '-Djava.awt.headless=true']
    tree = ET.parse(xml)
    tags = tree.getroot().find('tags')
    template = next(t for t in tags if t.get('characterID') == '670')
    ids = []
    for index, name in enumerate(footer):
        sid, tid = 8000 + index * 2, 8001 + index * 2
        text = copy.deepcopy(template)
        text.set('characterID', str(tid))
        text.set('hasText', 'true')
        text.set('initialText', footer[name]['text'])
        sprite = ET.Element('item', {'type': 'DefineSpriteTag', 'spriteId': str(sid), 'frameCount': '1'})
        children = ET.SubElement(sprite, 'subTags')
        ET.SubElement(children, 'item', {'type': 'PlaceObject2Tag', 'depth': '1', 'characterId': str(tid),
                                       'placeFlagHasCharacter': 'true', 'placeFlagMove': 'false'})
        ET.SubElement(children, 'item', {'type': 'ShowFrameTag'})
        tags.extend([text, sprite])
        ids.append(sid)
    derived = temporary / 'footer.xml'
    tree.write(derived, encoding='utf-8', xml_declaration=True)
    swf = derived.with_suffix('.swf')
    subprocess.run(java + ['-jar', str(jar), '-xml2swf', str(derived), str(swf)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(java + ['-jar', str(jar), '-zoom', '2', '-selectid', ','.join(map(str, ids)), '-export', 'sprite', str(temporary / 'footer-raster'), str(swf)], check=True, stdout=subprocess.DEVNULL)
    from PIL import Image
    for index, name in enumerate(footer):
        with Image.open(temporary / f'footer-raster/DefineSprite_{ids[index]}/1.png') as image:
            image.crop(image.getbbox()).save(output / footer[name]['texture'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--temporary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--raster-scale', type=int, default=2)
    parser.add_argument('--portraits-only', action='store_true',
                        help='Skip footer rebuilding and its optional Pillow dependency')
    parser.add_argument('names', nargs='+')
    args = parser.parse_args()
    if args.raster_scale < 1:
        parser.error('--raster-scale must be at least 1')
    build(args.workspace, args.temporary, args.output, args.ffdec, args.names,
          args.raster_scale, args.portraits_only)
