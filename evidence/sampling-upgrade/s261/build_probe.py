"""Build the exclusive Yijiao initCtrl unload observer on the locked s231 tape."""
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
SCRIPT = 'DefineSprite_455/frame_1/DoAction.as'
SOURCE_SHA = '46d0d657f9a9d5a7066ec2f65a058e47904d487733c605f02f18365e4c8935df'


def patch_fighter(source):
    needle = '      AImain.unloadMovie();'
    if source.count(needle) != 1:
        raise ValueError('missing unique authored unload')
    return source.replace(needle, '      _global.s261Observe("before_unload", AImain);\n' + needle + '\n      _global.s261Observe("after_unload", AImain);')


def patch_root(source):
    boundary = '   aiDisplay++;'
    if source.count(boundary) != 1:
        raise ValueError('missing unique root/sample boundaries')
    source = source.replace(boundary, boundary + '''
   if(_global.s261AwaitRoot && !_global.s261Zero)
   {
      _global.s261Observe("root", undefined);

   }''')
    return source


def patch_hooks(source):
    sample = '   _root.aiEvent("display_end",_root.aiDlCount);'
    if source.count(sample) != 1:
        raise ValueError('missing unique display sample boundary')
    source = source.replace(sample, sample + '''
   if(_global.s261Armed && !_global.s261Sampled)
   {
      _global.s261Observe("first_sample", undefined);
      _global.s261Sampled = true;
   }''')
    return (HERE / 'observer.as').read_text() + '\n' + source


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
    bundle = json.loads((ROOT / 'scripts/fighter/yijiao.json').read_text())
    original = next(s['source'] for s in bundle['scripts'] if s['path'] == SCRIPT)
    if hashlib.sha256(original.encode()).hexdigest() != SOURCE_SHA:
        raise ValueError('changed locked initCtrl source')
    subprocess.run([sys.executable, str(ROOT / 'tools/probes/build_ai_reference.py'),
                    '--ffdec', str(args.ffdec.resolve()), '--output', str(output),
                    '--run-id', args.run_id, '--frames', '60', '--move-case',
                    str(ROOT / 'evidence/sampling-upgrade/s231/yijiao__attack__neutral__ground__near.json'),
                    '--p1-character', '一角', '--p2-character', '一护',
                    '--p1-helper', '我爱罗', '--p2-helper', '魂', '--sampling-display'],
                   check=True, stdout=subprocess.DEVNULL)
    metadata = json.loads((output / 'build.json').read_text())
    diffs = []
    for name, path, transform in [('main', 'frame_1/DoAction.as', patch_hooks),
                                  ('main', 'frame_10/DoAction.as', patch_root),
                                  ('fighter/yijiao', SCRIPT, patch_fighter)]:
        patch = output / 'patches' / name / path
        before = patch.read_text()
        after = transform(before)
        patch.write_text(after)
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile='ordinary/' + name + '/' + path,
                                        tofile='s261/' + name + '/' + path))
        with (output / (name.replace('/', '-') + '-s261-build.log')).open('w') as log:
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
    metadata['s261_observer'] = {'source': 'fighter/yijiao#' + SCRIPT, 'scope': 'first P1 initCtrl unload only',
                                'build_elapsed_seconds': time.monotonic() - started}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(metadata['s261_observer']))


if __name__ == '__main__':
    main()
