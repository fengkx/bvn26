"""Observe an existing body action independently of the invoking helper continuation."""
import argparse
import difflib
import gzip
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('r23_parent', HERE.parent / 'native-fight-r21/build_observer.py')
r21 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r21)
base = r21.r19.r17.r14.r07.base
SITE = 'DefineSprite_638/frame_174/DoAction.as'
ORIGINAL = '动作 = 1;\r\n'


def patch(source, tag):
    if source != ORIGINAL or not re.fullmatch(r'[a-z0-9-]{10,80}', tag):
        raise ValueError('Target source/tag binding mismatch')
    # Body context supplies identity; no access to the initiating helper or logger.
    marker = ('trace("M002TARGET|' + tag + '|yihu638-frame174|" + '
              'escape(this._target) + "|" + this._currentframe);\n')
    return marker + source


def build(jar, output, tag):
    r21.build(jar, output, tag)
    report = json.loads((output / 'build.json').read_text())
    (output / 'r21-build.json').write_text(json.dumps(report, indent=2) + '\n')
    sources = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())['scripts']}
    source = sources[SITE]
    edited = patch(source, tag)
    directory = output / 'target'
    target = directory / 'scripts' / SITE
    target.parent.mkdir(parents=True)
    target.write_text(edited)
    movie = output / 'game/fighter/yihu.swf'
    before = output / 'yihu-r21.swf'
    shutil.copyfile(movie, before)
    command = ['java', '-Djava.awt.headless=true', '-jar', str(jar), '-importScript', str(before), str(movie), str(directory)]
    result = subprocess.run(command, capture_output=True)
    (directory / 'stdout').write_bytes(result.stdout)
    (directory / 'stderr').write_bytes(result.stderr)
    if result.returncode:
        raise ValueError('Target compilation failed')
    a, b = base.tags(before), base.tags(movie)
    changed = [k for k in a if a[k] != b.get(k)]
    if a.keys() != b.keys() or len(changed) != 1 or '/sprite638/' not in changed[0] or not changed[0].endswith(':12'):
        raise ValueError('Unexpected target tag scope')
    report['changed_tag_paths_by_asset']['game/fighter/yihu.swf'] += changed
    report['outputs_sha256']['game/fighter/yihu.swf'] = base.sha(movie)
    for name, expected in report['changed_tag_paths_by_asset'].items():
        a, b = base.tags(ROOT / name), base.tags(output / name)
        if a.keys() != b.keys() or set(k for k in a if a[k] != b[k]) != set(expected):
            raise ValueError('Original-to-copy tag scope mismatch')
    for name, digest in report['outputs_sha256'].items():
        if base.sha(output / name) != digest:
            raise ValueError('Copy hash mismatch')
    diff = ''.join(difflib.unified_diff(source.splitlines(True), edited.splitlines(True), fromfile=SITE, tofile=SITE + '.r23'))
    (output / 'target.diff.gz').write_bytes(gzip.compress(diff.encode(), mtime=0))
    report.update(facility='r23', live_validated=False, target_site=SITE,
                  target_command=command, target_exit=result.returncode,
                  target_builder_sha256=base.sha(Path(__file__)),
                  target_diff_sha256=base.sha(output / 'target.diff.gz'))
    (output / 'build.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    build(args.ffdec.resolve(), args.output.resolve(), args.run_id)
