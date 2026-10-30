"""Build the exclusive P1 receiver observer on the locked s64 tape."""
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
def patch_root(source):
    needle = '   _root.aiGeometrySample();'
    if source.count(needle) != 1:
        raise ValueError('missing unique geometry boundary')
    return source.replace(needle, '   _root.s256Observe();\n' + needle)


def patch_hooks(source):
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
    subprocess.run([sys.executable, str(ROOT / 'tools/probes/build_ai_reference.py'),
                    '--ffdec', str(args.ffdec.resolve()), '--output', str(output),
                    '--run-id', args.run_id, '--frames', '60', '--move-case',
                    str(ROOT / 'evidence/sampling-upgrade/s64/didala__summon__neutral__ground__near.json'),
                    '--p1-character', '迪达拉', '--p2-character', '一护',
                    '--p1-helper', '我爱罗', '--p2-helper', '魂', '--deidara-atm1-load-stamp'],
                   check=True, stdout=subprocess.DEVNULL)
    metadata = json.loads((output / 'build.json').read_text())
    diffs = []
    for name, path, transform in [('main', 'frame_1/DoAction.as', patch_hooks),
                                  ('main', 'frame_10/DoAction.as', patch_root)]:
        patch = output / 'patches' / name / path
        before = patch.read_text()
        after = transform(before)
        patch.write_text(after)
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile='ordinary/' + name + '/' + path,
                                        tofile='s256/' + name + '/' + path))
        with (output / (name.replace('/', '-') + '-s256-build.log')).open('w') as log:
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
    metadata['s256_observer'] = {'scope': 'P1 bdmn ticks 10-12 before geometry only',
                                'build_elapsed_seconds': time.monotonic() - started}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(metadata['s256_observer']))


if __name__ == '__main__':
    main()
