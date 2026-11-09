"""Observe two source consumption branches without certifying a global tick."""
import argparse
import difflib
import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('r12',HERE.parent/'native-fight-r12/build_observer.py')
r12=importlib.util.module_from_spec(spec);spec.loader.exec_module(r12)
r07=r12.r08.r07
DECISION=r07.DECISION
ORIGINAL='   if(nornalhit())\r\n   {\r\n      _parent.gotoAndPlay("砍1");\r\n   }'


def marker(kind,site):
    return '_root.__m002Emit("'+kind+'", escape(this._target) + "," + __m002Call + ",'+site+'," + escape(_parent._target) + "," + _root.__m002Value(_parent._currentframe) + "," + escape(_parent._parent.useAI));\n'


def patch_fighter(source):
    if source.count(ORIGINAL)!=2 or '__m002ConsumerSerial' in source:raise ValueError('Consumer inventory/collision')
    changes=[]
    for name,next_name in [('doStand','doAllAction'),('doAllAction','isPoFangAct')]:
        start=source.index('function '+name+'(');end=source.index('function '+next_name+'(',start+1)
        part=source[start:end]
        if part.count(ORIGINAL)!=1:raise ValueError('Consumer source binding changed')
        replacement='   var __m002Call = ++__m002ConsumerSerial;\n'+marker('consumer-query-before',name)
        replacement+='   if(_root.__m002ConsumerResult(nornalhit(),this,__m002Call,"'+name+'"))\r\n   {\r\n'
        replacement+=marker('consumer-goto-before',name)+'      _parent.gotoAndPlay("砍1");\n'+marker('consumer-goto-after',name)+'\r\n   }'
        source=source[:start]+part.replace(ORIGINAL,replacement,1)+source[end:]
        changes.append(dict(site=name,original=ORIGINAL,replacement=replacement))
    source+='\nvar __m002ConsumerSerial = 0;\n'
    return source,changes


def build(jar,output,run_id):
    r12.build(jar,output,run_id)
    base=r07.base;report=json.loads((output/'build.json').read_text())
    (output/'r12-build.json').write_text(json.dumps(report,indent=2)+'\n')
    boot=base.patch_sources(r07.sources('scripts/main.json'),run_id)[base.BOOT]+'\n'+(r07.HERE/'observer.as').read_text()
    fighter=r07.patch_fighter(r07.sources('scripts/fighter/yihu.json'))[0]
    patched,sites=patch_fighter(fighter)
    diffs=[]
    for asset,path,original,edited,expected in [
        ('main',base.BOOT,boot,boot+'\n'+(HERE/'observer.as').read_text(),['root/547:12']),
        ('fighter/yihu',DECISION,fighter,patched,['root/19:39/sprite16/1:12'])]:
        patch=output/('consumer-'+asset.replace('/','-'));target=patch/'scripts'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(edited)
        movie=output/'game'/f'{asset}.swf';before=output/(asset.replace('/','-')+'-r12.swf');shutil.copyfile(movie,before)
        command=['java','-Djava.awt.headless=true','-jar',str(jar),'-importScript',str(before),str(movie),str(patch)]
        run=subprocess.run(command,capture_output=True);(patch/'stdout').write_bytes(run.stdout);(patch/'stderr').write_bytes(run.stderr)
        if run.returncode:raise ValueError('Consumer compile failed')
        a,b=base.tags(before),base.tags(movie)
        if a.keys()!=b.keys() or [k for k in a if a[k]!=b[k]]!=expected:raise ValueError('Unexpected consumer tag change')
        original_tags=base.tags(ROOT/'game'/f'{asset}.swf')
        if [k for k in original_tags if original_tags[k]!=b[k]]!=report['changed_tag_paths_by_asset']['game/'+asset+'.swf']:raise ValueError('Original scope changed')
        report['outputs_sha256']['game/'+asset+'.swf']=base.sha(movie)
        diffs.extend(difflib.unified_diff(original.splitlines(True),edited.splitlines(True),fromfile=asset+'/'+path+'.r12',tofile=asset+'/'+path+'.r14'))
    for name,digest in report['outputs_sha256'].items():
        if base.sha(output/name)!=digest:raise ValueError('Unexpected copied asset change')
    (output/'consumer.diff.gz').write_bytes(gzip.compress(''.join(diffs).encode(),mtime=0))
    report.update(facility='r14',consumer_builder_sha256=base.sha(Path(__file__)),consumer_observer_sha256=base.sha(HERE/'observer.as'),
                  parent_r12_sha256=base.sha(output/'r12-build.json'),consumer_diff_sha256=base.sha(output/'consumer.diff.gz'),consumer_sites=[x['site'] for x in sites],
                  certified_global_tick=False,os_input_join_proven=False,production_admitted=False,native_parity_proven=False,oracle_accepted=False,live_validated=False)
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['changed_tag_paths_by_asset']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ffdec',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--run-id',required=True)
    a=p.parse_args();build(a.ffdec.resolve(),a.output.resolve(),a.run_id)
