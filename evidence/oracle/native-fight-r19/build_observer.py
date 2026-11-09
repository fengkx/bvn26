"""Add a direct Trace side channel without wrapping the native goto."""
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
spec = importlib.util.spec_from_file_location('r19_parent', HERE.parent / 'native-fight-r17/build_observer.py')
r17 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r17)


def patch_fighter(source):
    if '__m002Direct' in source:
        raise ValueError('Direct-channel collision')
    original = r17.GOTO + '      __m002ContinuationSink("continuation-breadcrumb", __m002ContinuationData);\n'
    if source.count(original) != 2:
        raise ValueError('Expected both exact continuation sites')
    replacement = ('      var __m002DirectBefore = "M002SIDE|" + __m002ContinuationData + "|before";\n'
                   '      var __m002DirectAfter = "M002SIDE|" + __m002ContinuationData + "|after";\n'
                   '      trace(__m002DirectBefore);\n' + r17.GOTO +
                   '      trace(__m002DirectAfter);\n'
                   '      __m002ContinuationSink("continuation-breadcrumb", __m002ContinuationData);\n')
    return source.replace(original, replacement), original, replacement


def build(jar, output, tag):
    r17.build(jar, output, tag)
    base = r17.r14.r07.base
    report = json.loads((output/'build.json').read_text())
    (output/'r17-build.json').write_text(json.dumps(report, indent=2)+'\n')
    source = r17.r14.patch_fighter(r17.r14.r07.patch_fighter(r17.r14.r07.sources('scripts/fighter/yihu.json'))[0])[0]
    source = r17.patch_fighter(source, tag)[0]
    edited, _, _ = patch_fighter(source)
    patch = output/'direct'; target = patch/'scripts'/r17.r14.DECISION
    target.parent.mkdir(parents=True); target.write_text(edited)
    movie = output/'game/fighter/yihu.swf'; before = output/'yihu-r17.swf'
    shutil.copyfile(movie, before)
    cmd = ['java','-Djava.awt.headless=true','-jar',str(jar),'-importScript',str(before),str(movie),str(patch)]
    run = subprocess.run(cmd,capture_output=True)
    (patch/'stdout').write_bytes(run.stdout); (patch/'stderr').write_bytes(run.stderr)
    if run.returncode: raise ValueError('Direct-channel compile failed')
    a,b = base.tags(before),base.tags(movie)
    if a.keys()!=b.keys() or [k for k in a if a[k]!=b[k]]!=['root/19:39/sprite16/1:12']:
        raise ValueError('Unexpected direct-channel scope')
    report['outputs_sha256']['game/fighter/yihu.swf']=base.sha(movie)
    for name,digest in report['outputs_sha256'].items():
        if base.sha(output/name)!=digest: raise ValueError('Copied asset mismatch')
    for name,expected in report['changed_tag_paths_by_asset'].items():
        a,b=base.tags(ROOT/name),base.tags(output/name)
        if a.keys()!=b.keys() or [k for k in a if a[k]!=b[k]]!=expected: raise ValueError('Original scope mismatch')
    (output/'direct.diff.gz').write_bytes(gzip.compress(''.join(difflib.unified_diff(source.splitlines(True),edited.splitlines(True),fromfile=r17.r14.DECISION+'.r17',tofile=r17.r14.DECISION+'.r19')).encode(),mtime=0))
    report.update(facility='r19',direct_builder_sha256=base.sha(Path(__file__)),direct_diff_sha256=base.sha(output/'direct.diff.gz'),parent_r17_sha256=base.sha(output/'r17-build.json'),live_validated=False)
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ffdec',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--run-id',required=True)
    a=p.parse_args();build(a.ffdec.resolve(),a.output.resolve(),a.run_id)
