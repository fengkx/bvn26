"""Bounded s258 observer extension; no authored statement or image boundary moves."""
import argparse
import difflib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

from tools.sampling_native import sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location('s258_builder', HERE.parent / 's258/build_probe.py')
s258 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s258)


def patch_root(source):
    return (HERE / 'observer.as').read_text() + s258.replace_once(
        source, '   _root.s258Observe("snapshot_before", _root.s258Timer);',
        '   _root.s262Snapshot();\n   _root.s258Observe("snapshot_before", _root.s258Timer);')


def patch_init(source, symbol):
    return f'_root.s262Init(this,{symbol});\n' + source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    started = time.monotonic()
    out = args.output.resolve()
    subprocess.run([sys.executable, str(HERE.parent / 's258/build_probe.py'),
                    '--ffdec', str(args.ffdec), '--output', str(out), '--run-id', args.run_id], check=True)
    source = {s['path']: s['source'].replace('\r\n', '\n') for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts']}
    diffs = []
    for path, symbol in [('frame_1/DoAction.as', None), ('DefineSprite_1813/frame_1/DoAction.as', 1813),
                         ('DefineSprite_1810/frame_1/DoAction.as', 1810)]:
        target = out / 'patches/main' / path
        before = target.read_text() if target.exists() else source[path]
        after = patch_root(before) if symbol is None else patch_init(before, symbol)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(after)
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile='s258/' + path, tofile='s262/' + path))
    with (out / 's262-build.log').open('w') as log:
        subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec), '-importScript',
                        str(ROOT / 'game/main.swf'), str(out / 'game/main.swf'), str(out / 'patches/main')],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    diff = out / 'instrumentation.diff'
    diff.write_text(diff.read_text() + ''.join(diffs))
    meta = json.loads((out / 'build.json').read_text())
    meta['instrumentation_sha256'] = sha(diff)
    meta['outputs_sha256']['game/main.swf'] = sha(out / 'game/main.swf')
    for path in [Path(__file__), HERE / 'observer.as']:
        meta['sources_sha256'][path.relative_to(ROOT).as_posix()] = sha(path)
    meta['s262_observer'] = {'build_elapsed_seconds': time.monotonic() - started,
                             'scope': 'timer/digit frame1 initialization and snapshot HUD/camera; not allocation identity'}
    (out / 'build.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(meta['s262_observer']))


if __name__ == '__main__':
    main()
