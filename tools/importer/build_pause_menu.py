"""Bake the original pause panel and Move List timeline; leave locked SWF inputs intact."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def build(xml, jar, workspace, output):
    root = ET.parse(xml)
    tags = root.getroot().find('tags')
    sprite = next(t for t in tags if t.get('spriteId') == '2010')
    source_frame_count = int(sprite.get('frameCount'))
    back = next(t for t in sprite.find('subTags') if t.get('characterId') == '2009').find('matrix')
    back_bounds = next(t for t in tags if t.get('shapeId') == '2008').find('shapeBounds')
    subtags = sprite.find('subTags')
    first = []
    for tag in subtags:
        if tag.get('name') == 'skk':
            selector = tag.find('matrix').attrib.copy()
            continue
        first.append(tag)
        if tag.get('type') == 'ShowFrameTag':
            break
    outer = next(t for t in tags if t.get('name') == 'game_menu').find('matrix')
    panel = next(t for t in first if t.get('characterId') == '1994').find('matrix')
    bounds = next(t for t in tags if t.get('shapeId') == '1993').find('shapeBounds')
    selector_bounds = next(t for t in tags if t.get('shapeId') == '2000').find('shapeBounds')
    scripts = json.loads(Path('scripts/main.json').read_text())['scripts']
    source = next(s['source'] for s in scripts if s['path'] == 'DefineSprite_1991/frame_1/DoAction.as')
    ys = json.loads(re.search(r'var _knys = (\[[^;]+\]);', source)[1])
    workspace.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    swf = workspace / 'panel.swf'
    java = ['java', '-Djava.awt.headless=true', '-jar', str(jar)]
    rect = json.loads(subprocess.check_output([
        'java', '-Djava.awt.headless=true', '-cp', str(jar),
        str(Path(__file__).with_name('SpriteBounds.java')), 'game/main.swf', '2010', str(swf),
    ], text=True))
    subprocess.run(java + ['-selectid', '2010,2001', '-export', 'sprite', str(workspace / 'raster'), str(swf)], check=True)
    for sid, name in [(2010, 'panel'), (2001, 'selector')]:
        shutil.copyfile(workspace / 'raster' / f'DefineSprite_{sid}' / '1.png', output / f'{name}.png')
    ox, oy = int(outer.get('translateX')) / 20, int(outer.get('translateY')) / 20
    spec = {
        'source_sha256': hashlib.sha256(Path('game/main.swf').read_bytes()).hexdigest(),
        'source': 'scripts/main.json::DefineSprite_1991/frame_1/DoAction.as',
        'panel_position': [ox + int(panel.get('translateX')) / 20 + int(bounds.get('Xmin')) / 20 * float(panel.get('scaleX')),
                           oy + int(panel.get('translateY')) / 20 + int(bounds.get('Ymin')) / 20 * float(panel.get('scaleY'))],
        'selector_position': [ox + (int(selector['translateX']) + int(selector_bounds.get('Xmin'))) / 20,
                              oy + int(selector_bounds.get('Ymin')) / 20],
        'selection_y': ys,
    }
    # Export the expanding panel and detail page directly from the locked SWF.
    original = workspace / 'original'
    subprocess.run(java + ['-selectid', '2010', '-export', 'sprite', str(original), 'game/main.swf'], check=True)
    for frame in range(2, source_frame_count + 1):
        shutil.copyfile(original / 'DefineSprite_2010' / f'{frame}.png', output / f'frame-{frame}.png')
    spec['detail_frame'] = source_frame_count
    spec['timeline_position'] = [ox + rect[0] / 20, oy + rect[1] / 20]
    spec['back_rect'] = [
        ox + (int(back.get('translateX')) + int(back_bounds.get('Xmin'))) / 20,
        oy + (int(back.get('translateY')) + int(back_bounds.get('Ymin'))) / 20,
        (int(back_bounds.get('Xmax')) - int(back_bounds.get('Xmin'))) / 20,
        (int(back_bounds.get('Ymax')) - int(back_bounds.get('Ymin'))) / 20,
    ]
    (output / 'presentation.json').write_text(json.dumps(spec, indent=2) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--xml', type=Path, required=True)
    p.add_argument('--ffdec-jar', type=Path, required=True)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    build(a.xml, a.ffdec_jar, a.workspace, a.output)
