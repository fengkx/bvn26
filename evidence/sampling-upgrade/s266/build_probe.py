"""Extend locked s263 with an authored defining-timeline control pair."""
import argparse
import copy
import difflib
import json
from pathlib import Path
import subprocess
import tarfile
import time
import xml.etree.ElementTree as ET

from tools.sampling_native import sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def build(out, ffdec):
    started = time.monotonic()
    out.mkdir(parents=True, exist_ok=False)
    for name in ('s257/native-build.tar.gz', 's263/build-extension.tar.gz'):
        with tarfile.open(HERE.parent / name) as archive:
            archive.extractall(out, filter='data')
    meta = json.loads((out / 'build.json').read_text())
    for name, digest in meta['outputs_sha256'].items():
        if sha(out / name) != digest:
            raise ValueError('locked build mismatch: ' + name)
    for name, digest in meta['sources_sha256'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('locked source mismatch: ' + name)

    def java(*args):
        with (out / 's266-build.log').open('a') as log:
            subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec), *map(str, args)],
                           stdout=log, stderr=subprocess.STDOUT, check=True)

    java('-swf2xml', out / 'game/main.swf', out / 'main.xml')
    tree = ET.parse(out / 'main.xml')
    tags = tree.getroot().find('tags')
    if any(n.get('characterId') in ('60000', '60001') or n.get('spriteId') in ('60000', '60001') for n in tree.iter()):
        raise ValueError('probe character ID collision')
    if any(n.get('depth') in ('30000', '30001') for n in tags):
        raise ValueError('probe root depth collision')
    template = next(n for n in tree.iter('item') if n.get('type') == 'PlaceObject2Tag' and n.get('placeFlagHasClipActions') == 'false' and n.get('placeFlagHasColorTransform') == 'false')

    def place(character, depth, name):
        n = copy.deepcopy(template)
        n.attrib.update(characterId=str(character), depth=str(depth), name=name,
                        placeFlagHasName='true', placeFlagMove='false', placeFlagHasCharacter='true',
                        placeFlagHasRatio='false', placeFlagHasClipDepth='false')
        for child in list(n):
            n.remove(child)
        ET.SubElement(n, 'matrix', dict(type='MATRIX', hasRotate='false', hasScale='false',
                                      nRotateBits='0', nScaleBits='0', nTranslateBits='0', translateX='0', translateY='0'))
        return n

    def tag(parent, kind, **attrs):
        return ET.SubElement(parent, 'item', dict(type=kind, forceWriteAsLong='false', **attrs))

    child = ET.Element('item', dict(type='DefineSpriteTag', forceWriteAsLong='true', frameCount='1', hasEndTag='true', spriteId='60000'))
    sub = ET.SubElement(child, 'subTags')
    tag(sub, 'DoActionTag', actionBytes='0700')
    tag(sub, 'ShowFrameTag')
    parent = ET.Element('item', dict(type='DefineSpriteTag', forceWriteAsLong='true', frameCount='3', hasEndTag='true', spriteId='60001'))
    sub = ET.SubElement(parent, 'subTags')
    sub.append(place(60000, 1, 'child'))
    tag(sub, 'DoActionTag', actionBytes='0700')
    tag(sub, 'ShowFrameTag')
    tag(sub, 'ShowFrameTag')
    tag(sub, 'RemoveObject2Tag', depth='1')
    tag(sub, 'ShowFrameTag')
    first_show = next(i for i, n in enumerate(tags) if n.get('type') == 'ShowFrameTag')
    for offset, node in enumerate((child, parent, place(60001, 30000, 's266Retain'), place(60001, 30001, 's266Remove'))):
        tags.insert(first_show + offset, node)
    tree.write(out / 'authored.xml', encoding='utf-8', xml_declaration=True)
    java('-xml2swf', out / 'authored.xml', out / 'authored.swf')
    patches = out / 's266-patches'
    diffs = []
    for relative in ('frame_1/DoAction.as', 'frame_10/DoAction.as', 'DefineSprite_60000/frame_1/DoAction.as'):
        before = (out / 'patches/main' / relative).read_text() if not relative.startswith('DefineSprite') else 'stop();\n'
        after = before.replace(meta['run_id'], 's266-context-r02')
        if relative == 'frame_1/DoAction.as':
            after += '\n' + (HERE / 'control.as').read_text()
        elif relative == 'frame_10/DoAction.as':
            needle = '   if(aiFight == 10) _global.s263Run();'
            if after.count(needle) != 1:
                raise ValueError('missing s263 invocation')
            after = after.replace(needle, needle + '\n   if(aiFight == 10) _global.s266Run();')
        else:
            after = (HERE / 'worker.as').read_text()
        dest = patches / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(after)
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='s263/' + relative, tofile='s266/' + relative))
    java('-importScript', out / 'authored.swf', out / 'game/main.swf', patches)
    diff = out / 'instrumentation.diff'
    diff.write_text(diff.read_text() + '\nS266: append synthetic authored Sprite60000/60001 and root placements30000/30001. Parent frame2 retains child; frame3 removes depth1.\n' + ''.join(diffs))
    meta['run_id'] = 's266-context-r02'
    meta['outputs_sha256']['game/main.swf'] = sha(out / 'game/main.swf')
    meta['instrumentation_sha256'] = sha(diff)
    for path in (Path(__file__), HERE / 'control.as', HERE / 'worker.as'):
        meta['sources_sha256'][str(path.relative_to(ROOT))] = sha(path)
    meta['s266_control'] = {'base_archive_sha256': sha(HERE.parent / 's263/build-extension.tar.gz'),
                           'build_elapsed_seconds': time.monotonic() - started, 'ffdec_sha256': sha(ffdec),
                           'scope': 'synthetic authored defining child; retained/removing parent goto; Chad bytes unchanged'}
    (out / 'build.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(meta['s266_control']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    args = parser.parse_args()
    build(args.output.resolve(), args.ffdec.resolve())
