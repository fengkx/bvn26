"""Extend the locked s262 build with one placement observer, without images."""
import argparse
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
    start = time.monotonic()
    out.mkdir(parents=True, exist_ok=False)
    with tarfile.open(HERE.parent / 's262/native-build.tar.gz') as archive:
        archive.extractall(out, filter='data')
    meta = json.loads((out / 'build.json').read_text())
    for name, digest in meta['outputs_sha256'].items():
        if sha(out / name) != digest:
            raise ValueError('locked build mismatch: ' + name)
    for name, digest in meta['sources_sha256'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('locked source mismatch: ' + name)
    def java(*args):
        with (out / 's265-build.log').open('a') as log:
            subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(ffdec), *map(str, args)],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
    java('-swf2xml', out / 'game/main.swf', out / 'main.xml')
    tree = ET.parse(out / 'main.xml')
    sprite = next(n for n in tree.iter('item') if n.get('type') == 'DefineSpriteTag' and n.get('spriteId') == '1813')
    placement = next(n for n in sprite.find('subTags') if n.get('name') == '个')
    if placement.get('depth') != '3' or placement.get('characterId') != '1810' or placement.get('placeFlagHasClipActions') != 'false':
        raise ValueError('changed authored placement')
    template = next(n for n in tree.iter('allEventFlags'))
    flags = {k: ('false' if v in ('true', 'false') else v) for k, v in template.attrib.items()}
    clip = ET.SubElement(placement, 'clipActions', {'type': 'CLIPACTIONS', 'reserved': '0'})
    ET.SubElement(clip, 'allEventFlags', dict(flags, clipEventLoad='true', clipEventUnload='true'))
    records = ET.SubElement(clip, 'clipActionRecords')
    for event in ('Load', 'Unload'):
        record = ET.SubElement(records, 'item', {'type': 'CLIPACTIONRECORD', 'actionBytes': '00', 'keyCode': '0'})
        ET.SubElement(record, 'eventFlags', dict(flags, **{'clipEvent' + event: 'true'}))
    placement.set('placeFlagHasClipActions', 'true')
    tree.write(out / 'observed.xml', encoding='utf-8', xml_declaration=True)
    java('-xml2swf', out / 'observed.xml', out / 'observed.swf')
    patches = out / 's265-patches'
    diffs = []
    def patch(path, before, after):
        dest = patches / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(after)
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='s262/' + path, tofile='s265/' + path))
    path = 'frame_1/DoAction.as'
    before = (out / 'patches/main' / path).read_text()
    left = before.index('_root.aiBitmapSample = function()')
    right = before.index('_root.aiHelperClipFrame = function(', left)
    after = before[:left] + '_root.aiBitmapSample = function() { _root.s265Sample(); };\n' + before[right:]
    after = after.replace(meta['run_id'], 's265-lifetime-r01')
    after = after.replace('/private/tmp/bvn-s262-r01-build', str(out)).replace('/tmp/bvn-s262-r01-build', str(out))
    patch(path, before, (HERE / 'observer.as').read_text() + after)
    path = 'DefineSprite_1810/frame_1/DoAction.as'
    before = (out / 'patches/main' / path).read_text()
    patch(path, before, '_root.s265Entry(this);\n' + before)
    for event in ('load', 'unload'):
        path = f'DefineSprite_1813/frame_1/PlaceObject2_1810_3/CLIPACTIONRECORD onClipEvent({event}).as'
        patch(path, '', f'onClipEvent({event}) {{ _root.s265Life(this,"{event}"); }}\n')
    java('-importScript', out / 'observed.swf', out / 'game/main.swf', patches)
    instrumentation = out / 'instrumentation.diff'
    instrumentation.write_text(instrumentation.read_text() + '\nS265: add load/unload records to Sprite1813 frame1 depth3; no placement fields changed.\n' + ''.join(diffs))
    meta['run_id'] = 's265-lifetime-r01'
    meta['outputs_sha256']['game/main.swf'] = sha(out / 'game/main.swf')
    meta['instrumentation_sha256'] = sha(instrumentation)
    for path in (Path(__file__), HERE / 'observer.as'):
        meta['sources_sha256'][str(path.relative_to(ROOT))] = sha(path)
    meta['s265_observer'] = {'images_written': 0, 'draw_executed': False, 'encoding_executed': False,
                             'build_elapsed_seconds': time.monotonic() - start,
                             'ffdec_sha256': sha(ffdec), 'scope': 'ones placement load/unload and duplicate retained/replaced controls; no encoding control'}
    (out / 'build.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(meta['s265_observer']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    args = parser.parse_args()
    build(args.output.resolve(), args.ffdec.resolve())
