"""Prepare lexical continuation breadcrumbs on independent temporary copies."""
import argparse
import difflib
import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('r17_parent', HERE.parent / 'native-fight-r14/build_observer.py')
r14 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r14)
GOTO = '      _parent.gotoAndPlay("砍1");\n'


def patch_fighter(source, run_id):
    if '__m002Continuation' in source or source.count(GOTO) != 2:
        raise ValueError('Unexpected continuation source inventory')
    if not run_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in run_id):
        raise ValueError('Unsafe run tag')
    changes = []
    for site in ('doStand', 'doAllAction'):
        original = r14.marker('consumer-goto-before', site) + GOTO + r14.marker('consumer-goto-after', site)
        if source.count(original) != 1:
            raise ValueError('Source binding mismatch')
        prep = ('      var __m002ContinuationSink = _root.__m002Emit;\n'
                '      var __m002ContinuationData = "' + run_id + '," + escape(this._target) + "," + __m002Call + ",' + site + '";\n'
                '      __m002ContinuationSink("continuation-prep", __m002ContinuationData);\n')
        breadcrumb = '      __m002ContinuationSink("continuation-breadcrumb", __m002ContinuationData);\n'
        replacement = r14.marker('consumer-goto-before', site) + prep + GOTO + breadcrumb + r14.marker('consumer-goto-after', site)
        source = source.replace(original, replacement, 1)
        changes.append(dict(site=site, original=original, replacement=replacement))
    return source, changes


def build(jar, output, run_id):
    r14.build(jar, output, run_id)
    base = r14.r07.base
    report = json.loads((output / 'build.json').read_text())
    (output / 'r14-build.json').write_text(json.dumps(report, indent=2) + '\n')
    original = r14.patch_fighter(r14.r07.patch_fighter(r14.r07.sources('scripts/fighter/yihu.json'))[0])[0]
    edited, changes = patch_fighter(original, run_id)
    patch = output / 'continuation'
    target = patch / 'scripts' / r14.DECISION
    target.parent.mkdir(parents=True)
    target.write_text(edited)
    movie = output / 'game/fighter/yihu.swf'
    before = output / 'yihu-r14.swf'
    shutil.copyfile(movie, before)
    run = subprocess.run(['java', '-Djava.awt.headless=true', '-jar', str(jar), '-importScript', str(before), str(movie), str(patch)], capture_output=True)
    (patch / 'stdout').write_bytes(run.stdout)
    (patch / 'stderr').write_bytes(run.stderr)
    if run.returncode:
        raise ValueError('Continuation compilation failed')
    a, b = base.tags(before), base.tags(movie)
    changed = [k for k in a if a[k] != b.get(k)]
    if a.keys() != b.keys() or changed != ['root/19:39/sprite16/1:12']:
        raise ValueError('Unexpected continuation tag changes')
    locked = base.tags(ROOT / 'game/fighter/yihu.swf')
    if locked.keys() != b.keys() or [k for k in locked if locked[k] != b[k]] != report['changed_tag_paths_by_asset']['game/fighter/yihu.swf']:
        raise ValueError('Original audit scope changed')
    report['outputs_sha256']['game/fighter/yihu.swf'] = base.sha(movie)
    for name, digest in report['outputs_sha256'].items():
        if base.sha(output / name) != digest:
            raise ValueError('Copied asset changed unexpectedly')
    diff = ''.join(difflib.unified_diff(original.splitlines(True), edited.splitlines(True), fromfile=r14.DECISION+'.r14', tofile=r14.DECISION+'.r17'))
    (output / 'continuation.diff.gz').write_bytes(gzip.compress(diff.encode(), mtime=0))
    report.update(facility='r17', continuation_builder_sha256=base.sha(Path(__file__)),
                  continuation_diff_sha256=base.sha(output / 'continuation.diff.gz'),
                  parent_r14_sha256=base.sha(output / 'r14-build.json'), continuation_sites=[c['site'] for c in changes],
                  continuation_changed_tags=changed, live_validated=False)
    (output / 'build.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    build(args.ffdec.resolve(), args.output.resolve(), args.run_id)
