"""Instrument only Sprite1813 countdown and the unchanged bitmap draw boundary."""
import argparse
import difflib
import json
from pathlib import Path
import subprocess
import sys
import time

from tools.probes.build_ai_reference import ROOT
from tools.sampling_native import sha

HERE = Path(__file__).resolve().parent
TIMER = 'DefineSprite_1813/frame_1/DoAction.as'
CASE = ROOT / 'evidence/sampling-upgrade/s220/sasuke__attack__neutral__ground__near.json'


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('missing unique boundary: ' + old)
    return source.replace(old, new)


HOOK = '''
_root.s258Count = 0;
_root.s258Observe = function(phase, receiver)
{
   var timer = _root.s258Timer;
   _root.aiEvent("s258_countdown", phase + "," + _root.s258Count + "," + String(receiver) + "," + String(timer) + "," + _root.timeset + "," + _root.gametime + "," + _root.zhanting + "," + _root.game.p1.mc.sw + "," + _root.game.p2.mc.sw + "," + _root.modo + "," + timer.十._currentframe + "," + timer.个._currentframe + "," + timer._currentframe);
};
'''


def patch_timer(source):
    source = replace_once(source, 'time = function()\n{', '''_root.s258Timer = this;
time = function()
{
   _root.s258Count++;
   _root.s258Observe("fire_before", this);''')
    source = replace_once(source, '   个.gotoAndStop(gs + 1);',
                          '   个.gotoAndStop(gs + 1);\n   _root.s258Observe("fire_after", this);')
    return replace_once(source, '   _root.timeset = setInterval(time,1000);', '''   _root.s258Observe("register_before", this);
   _root.timeset = setInterval(time,1000);
   _root.s258Observe("register_after", this);''')


def patch_root(source):
    source = replace_once(source, '   image.draw(_root);', '''   _root.s258Observe("snapshot_before", _root.s258Timer);
   image.draw(_root);
   _root.s258Observe("snapshot_after", _root.s258Timer);''')
    return HOOK + source


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
                    '--run-id', args.run_id, '--frames', '60', '--move-case', str(CASE),
                    '--p1-character', '佐助', '--p2-character', '一护',
                    '--p1-helper', '我爱罗', '--p2-helper', '魂', '--sampling-bitmap'],
                   check=True, stdout=subprocess.DEVNULL)
    metadata = json.loads((output / 'build.json').read_text())
    timer = next(s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts'] if s['path'] == TIMER)
    diffs = []
    for path, before, after in [
        (TIMER, timer.replace('\r\n', '\n'), patch_timer(timer.replace('\r\n', '\n'))),
        ('frame_1/DoAction.as', (output / 'patches/main/frame_1/DoAction.as').read_text(),
         patch_root((output / 'patches/main/frame_1/DoAction.as').read_text()))]:
        target = output / 'patches/main' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(after)
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile='ordinary/main/' + path, tofile='s258/main/' + path))
    with (output / 's258-build.log').open('w') as log:
        subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec.resolve()),
                        '-importScript', str(ROOT / 'game/main.swf'), str(output / 'game/main.swf'),
                        str(output / 'patches/main')], stdout=log, stderr=subprocess.STDOUT, check=True)
    instrumentation = output / 'instrumentation.diff'
    instrumentation.write_text(instrumentation.read_text() + ''.join(diffs))
    metadata['instrumentation_sha256'] = sha(instrumentation)
    metadata['outputs_sha256']['game/main.swf'] = sha(output / 'game/main.swf')
    metadata['sources_sha256'][Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    metadata['s258_observer'] = {'scope': 'one Sprite1813 callback, unchanged bitmap draw',
                                'build_elapsed_seconds': time.monotonic() - started}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(metadata['s258_observer']))


if __name__ == '__main__':
    main()
