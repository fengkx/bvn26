"""Extend the locked s257 build with an isolated register invalidation control."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch_root(source):
    needle = '   if(aiFight >= 10 && aiFight <= 12)'
    if source.count(needle) != 1:
        raise ValueError('missing unique s257 root boundary')
    return source.replace(needle, '   if(aiFight == 10) _global.s263Run();\n' + needle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    started = time.monotonic()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with tarfile.open(HERE.parent / 's257/native-build.tar.gz') as archive:
        archive.extractall(output, filter='data')
    metadata = json.loads((output / 'build.json').read_text())
    old_run = metadata['run_id']
    diffs = []
    for relative in ('frame_1/DoAction.as', 'frame_10/DoAction.as'):
        path = output / 'patches/main' / relative
        before = path.read_text()
        after = before.replace(old_run, args.run_id)
        if relative == 'frame_1/DoAction.as':
            after += '\n' + (HERE / 'control.as').read_text()
        else:
            after = patch_root(after)
        path.write_text(after)
        diffs.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile='s257/' + relative, tofile='s263/' + relative))
    with (output / 's263-build.log').open('w') as log:
        subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(args.ffdec.resolve()),
                        '-importScript', str(ROOT / 'game/main.swf'), str(output / 'game/main.swf'),
                        str(output / 'patches/main')], check=True, stdout=log, stderr=subprocess.STDOUT)
    metadata['run_id'] = args.run_id
    metadata['outputs_sha256']['game/main.swf'] = sha(output / 'game/main.swf')
    diff = output / 'instrumentation.diff'
    diff.write_text(diff.read_text() + ''.join(diffs))
    metadata['instrumentation_sha256'] = sha(diff)
    for path in (Path(__file__), HERE / 'control.as'):
        metadata['sources_sha256'][path.relative_to(ROOT).as_posix()] = sha(path)
    metadata['s263_control'] = {'base_archive_sha256': sha(HERE.parent / 's257/native-build.tar.gz'),
                               'build_elapsed_seconds': time.monotonic() - started,
                               'scope': 'isolated dynamic clip retain/remove register access; Chad SWF unchanged'}
    (output / 'build.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(metadata['s263_control']))


if __name__ == '__main__':
    main()
