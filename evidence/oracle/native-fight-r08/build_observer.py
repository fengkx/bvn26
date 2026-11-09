"""Add only existing source-local boundaries to the immutable r07 build."""
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
spec=importlib.util.spec_from_file_location('r07',HERE.parent/'native-fight-r07/build_observer.py')
r07=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r07)
LOADER='DefineSprite_1900/frame_1/DoAction.as'
INIT='frame_8/DoAction.as'
REQUEST='_this._loader.loadClip(_root.fighterDir + _loc3_.url,_root.game[pr]);'
CALLBACK='LO.onLoadComplete = function(target)\r\n{\r\n   loadStep++;\r\n   loadSteps[loadStep]();\r\n};'
HP='_root.game.p1.mc.hp = _root.game.p2.mc.hp = _root.maxhp;'
REQUEST_MARK='_root.__m002Emit("loader-request", escape(pr) + "," + escape(_root[pr + "selt"]) + "," + escape(_root.fighterDir + _loc3_.url) + "," + escape(_root.game[pr]._target));\n'
CALLBACK_ENTRY='_root.__m002Emit("load-complete-entry", escape(target._target) + "," + loadStep);\n'
CALLBACK_EXIT='\n_root.__m002Emit("load-complete-exit", escape(target._target) + "," + loadStep);'


def hp_marker(boundary):
    return '_root.__m002Emit("chushi-hp-'+boundary+'", _root.__m002Value(_root.maxhp) + "," + _root.zhanting + "," + _root.gamePaused);\n_root.__m002State("p1");\n_root.__m002State("p2");\n'


def patch_sources(sources, run_id, require_on_load_init=False):
    if any('onLoadInit' in s for s in sources.values()):
        raise ValueError('Unexpected onLoadInit; re-audit actual callback')
    if require_on_load_init:
        raise ValueError('No existing onLoadInit callback in locked main source')
    loader=r07.base.patch_sources(sources,run_id)[LOADER]
    init=sources[INIT]
    if loader.count(REQUEST)!=1 or loader.count(CALLBACK)!=1 or init.count(HP)!=1 or init.count('var chushi = function()')!=1:
        raise ValueError('Source boundary missing or ambiguous')
    loader=loader.replace(REQUEST,REQUEST_MARK+REQUEST,1)
    callback=CALLBACK.replace('{\r\n','{\r\n'+CALLBACK_ENTRY,1).replace('\r\n};',CALLBACK_EXIT+'\r\n};',1)
    loader=loader.replace(CALLBACK,callback,1)
    init=init.replace(HP,hp_marker('before')+HP+'\n'+hp_marker('after'),1)
    return {LOADER:loader,INIT:init}


def root_action(tags, frame):
    current=1
    found=[]
    for key in tags:
        if key.count('/')!=1:continue
        kind=int(key.rsplit(':',1)[1])
        if kind==12 and current==frame:found.append(key)
        if kind==1:current+=1
    if len(found)!=1:raise ValueError('Ambiguous root frame action')
    return found[0]


def build(jar,output,run_id):
    r07.build(jar,output,run_id)
    report=json.loads((output/'build.json').read_text())
    (output/'r07-build.json').write_text(json.dumps(report,indent=2)+'\n')
    sources=r07.sources('scripts/main.json')
    edits=patch_sources(sources,run_id)
    patch=output/'markers'
    diffs=[]
    previous=r07.base.patch_sources(sources,run_id)
    for path,source in edits.items():
        target=patch/'scripts'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source)
        diffs.extend(difflib.unified_diff(previous.get(path,sources[path]).splitlines(True),source.splitlines(True),fromfile=path+'.r07',tofile=path+'.r08'))
    movie=output/'game/main.swf';before=output/'r07-main.swf';shutil.copyfile(movie,before)
    command=['java','-Djava.awt.headless=true','-jar',str(jar),'-importScript',str(before),str(movie),str(patch)]
    result=subprocess.run(command,capture_output=True)
    (output/'markers.stdout').write_bytes(result.stdout);(output/'markers.stderr').write_bytes(result.stderr)
    if result.returncode:raise ValueError('Marker compilation failed')
    a,b=r07.base.tags(before),r07.base.tags(movie)
    expected={root_action(a,8),'root/2106:39/sprite1900/1:12'}
    if a.keys()!=b.keys() or {k for k in a if a[k]!=b[k]}!=expected:raise ValueError('Unexpected marker tag changes')
    original=r07.base.tags(ROOT/'game/main.swf')
    report['changed_tag_paths_by_asset']['game/main.swf']=[k for k in original if original[k]!=b[k]]
    report['outputs_sha256']['game/main.swf']=r07.base.sha(movie)
    for name,digest in report['outputs_sha256'].items():
        if r07.base.sha(output/name)!=digest:raise ValueError('Unexpected output mutation')
    (output/'markers.diff.gz').write_bytes(gzip.compress(''.join(diffs).encode(),mtime=0))
    report.update(facility='r08',marker_command=command,marker_diff_sha256=r07.base.sha(output/'markers.diff.gz'),
                  parent_build_sha256=r07.base.sha(output/'r07-build.json'),marker_builder_sha256=r07.base.sha(Path(__file__)),
                  existing_onLoadInit=False,onLoadComplete_is_not_onLoadInit=True,source_sites=report['source_sites']+[INIT])
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['changed_tag_paths_by_asset']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ffdec',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--run-id',required=True)
    a=p.parse_args();build(a.ffdec.resolve(),a.output.resolve(),a.run_id)
