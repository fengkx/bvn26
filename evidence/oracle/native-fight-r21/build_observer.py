"""Prepare literal Trace markers that do not read post-goto locals."""
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
spec = importlib.util.spec_from_file_location('r21_parent', HERE.parent / 'native-fight-r19/build_observer.py')
r19 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r19)


def patch_fighter(source, tag):
    if not tag or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in tag):
        raise ValueError('Unsafe tag')
    if 'M002LITERAL|' in source:
        raise ValueError('Literal channel collision')
    original = r19.r17.GOTO + '      trace(__m002DirectAfter);\n'
    changes=[]
    for site, following in [('doStand','doAllAction'),('doAllAction','isPoFangAct')]:
        start=source.index('function '+site+'(');end=source.index('function '+following+'(',start+1)
        part=source[start:end]
        if part.count(original)!=1:raise ValueError('Literal source binding mismatch')
        replacement=('      trace("M002LITERAL|'+tag+'|'+site+'|before");\n'+r19.r17.GOTO+
                     '      trace("M002LITERAL|'+tag+'|'+site+'|after");\n'+
                     '      trace(__m002DirectAfter);\n')
        source=source[:start]+part.replace(original,replacement,1)+source[end:]
        changes.append(dict(site=site,original=original,replacement=replacement))
    return source,changes


def build(jar, output, tag):
    r19.build(jar, output, tag)
    base = r19.r17.r14.r07.base
    report = json.loads((output/'build.json').read_text())
    (output/'r19-build.json').write_text(json.dumps(report, indent=2)+'\n')
    source = r19.r17.r14.patch_fighter(r19.r17.r14.r07.patch_fighter(r19.r17.r14.r07.sources('scripts/fighter/yihu.json'))[0])[0]
    source = r19.r17.patch_fighter(source, tag)[0]
    source = r19.patch_fighter(source)[0]
    edited, _ = patch_fighter(source, tag)
    patch = output/'literal'; target = patch/'scripts'/r19.r17.r14.DECISION
    target.parent.mkdir(parents=True); target.write_text(edited)
    movie = output/'game/fighter/yihu.swf'; before = output/'yihu-r19.swf'
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
    (output/'literal.diff.gz').write_bytes(gzip.compress(''.join(difflib.unified_diff(source.splitlines(True),edited.splitlines(True),fromfile=r19.r17.r14.DECISION+'.r19',tofile=r19.r17.r14.DECISION+'.r21')).encode(),mtime=0))
    report.update(facility='r21',literal_builder_sha256=base.sha(Path(__file__)),literal_diff_sha256=base.sha(output/'literal.diff.gz'),parent_r19_sha256=base.sha(output/'r19-build.json'),live_validated=False)
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ffdec',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--run-id',required=True)
    a=p.parse_args();build(a.ffdec.resolve(),a.output.resolve(),a.run_id)
