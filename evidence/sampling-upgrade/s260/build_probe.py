"""Build bounded receiver initialization observations on the locked s256 tape."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from tools.probes.build_ai_reference import ROOT
from tools.sampling_native import sha

HERE = Path(__file__).resolve().parent
CONTROLLER = 'DefineSprite_16/frame_1/DoAction.as'
RECEIVER = 'DefineSprite_2/frame_1/DoAction.as'
ENTER_FRAME = 'DefineSprite_542/frame_840/PlaceObject2_2_29/CLIPACTIONRECORD onClipEvent(enterFrame).as'


def replace_once(source, needle, replacement):
    if source.count(needle) != 1:
        raise ValueError('missing unique boundary: ' + needle)
    return source.replace(needle, replacement)


def observe(phase, target):
    return '_root.s260Observe("' + phase + '",' + target + ');'


def patch_root(source):
    needle = '   _root.aiGeometrySample();'
    return replace_once(source, needle, '   ' + observe('root_before_geometry', '_root.game.p1.mc.bdmn') + '\n' + needle)


def patch_hooks(source):
    return (HERE / 'observer.as').read_text() + '\n' + source


def patch_controller(source):
    needle = '      _parent.gotoAndPlay("招换");'
    return replace_once(source, needle,
                        '      ' + observe('jump_before', '_parent.bdmn') + '\n' + needle +
                        '\n      ' + observe('jump_after', '_root.game.p1.mc.bdmn'))


def patch_receiver(source):
    return observe('frame1_entry', 'this') + '\n' + source + '\n' + observe('frame1_exit', 'this') + '\n'


def patch_enter_frame(source):
    return replace_once(source, '   beida();', '   ' + observe('enterFrame_before', 'this') +
                        '\n   beida();\n   ' + observe('enterFrame_after', 'this'))


def patch_destination(source):
    return observe('frame840_entry', 'bdmn') + '\n' + source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    started = time.monotonic()
    output = args.output.resolve()
    if output.exists():
        raise ValueError('use a fresh output directory')
    subprocess.run([sys.executable, str(ROOT / 'tools/probes/build_ai_reference.py'),
                    '--ffdec', str(args.ffdec.resolve()), '--output', str(output),
                    '--run-id', args.run_id, '--frames', '60', '--move-case',
                    str(ROOT / 'evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json'),
                    '--p1-character', '迪达拉', '--p2-character', '一护',
                    '--p1-helper', '我爱罗', '--p2-helper', '魂', '--deidara-atm1-load-stamp'],
                   check=True, stdout=subprocess.DEVNULL)
    metadata = json.loads((output / 'build.json').read_text())
    diffs = []
    edits = [('main', 'frame_1/DoAction.as', patch_hooks),
             ('main', 'frame_10/DoAction.as', patch_root),
             ('fighter/didala', CONTROLLER, patch_controller),
             ('fighter/didala', RECEIVER, patch_receiver),
             ('fighter/didala', ENTER_FRAME, patch_enter_frame),
             ('fighter/didala', 'DefineSprite_542/frame_840/DoAction.as', patch_destination)]
    bundle = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/fighter/didala.json').read_text())['scripts']}
    for name, path, transform in edits:
        patch = output / 'patches' / name / path
        before = patch.read_text() if patch.exists() else bundle[path]
        patch.parent.mkdir(parents=True, exist_ok=True)
        after = transform(before)
        patch.write_text(after)
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile='ordinary/' + name + '/' + path,
                                        tofile='s260/' + name + '/' + path))
    for name in ('main', 'fighter/didala'):
        with (output / (name.replace('/', '-') + '-s260-build.log')).open('w') as log:
            subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec.resolve()),
                            '-importScript', str(ROOT / 'game' / (name + '.swf')),
                            str(output / 'game' / (name + '.swf')), str(output / 'patches' / name)],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        metadata['outputs_sha256']['game/' + name + '.swf'] = sha(output / 'game' / (name + '.swf'))
    instrumentation = output / 'instrumentation.diff'
    instrumentation.write_text(instrumentation.read_text() + ''.join(diffs))
    metadata['instrumentation_sha256'] = sha(instrumentation)
    for path in (Path(__file__), HERE / 'observer.as'):
        metadata['sources_sha256'][path.relative_to(ROOT).as_posix()] = sha(path)
    metadata['s260_observer'] = {'scope': 'P1 bdmn ticks 10-12: authored goto, frame1, frame840, enterFrame and unchanged geometry boundary',
                                'build_elapsed_seconds': time.monotonic() - started}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(metadata['s260_observer']))


if __name__ == '__main__':
    main()
