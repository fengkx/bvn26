"""Observe existing startFight/menu source boundaries in a temporary r08 copy."""
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
spec=importlib.util.spec_from_file_location('r08',HERE.parent/'native-fight-r08/build_observer.py')
r08=importlib.util.module_from_spec(spec);spec.loader.exec_module(r08)
FRAME='frame_8/DoAction.as'
START='function startFight()\r\n{\r\n   _root.zhanting = false;\r\n   _root.readying = false;\r\n   _root.setMenuEnable(true);\r\n}'
MENU='function setMenuEnable(v)\r\n{\r\n   _menuEnabled = v;\r\n   if(!v)\r\n   {\r\n      if(_root.game_menu)\r\n      {\r\n         _root.game_menu._visible = false;\r\n      }\r\n   }\r\n}'


def state_marker(kind,actors=False):
    source='_root.__m002Emit("'+kind+'", escape(_root.zhanting) + "," + escape(_root.readying) + "," + escape(_menuEnabled) + "," + escape(_root.gamePaused) + "," + escape(_root.p2loaded) + "," + _root._currentframe);\n'
    if actors:source+='_root.__m002State("p1");\n_root.__m002State("p2");\n'
    return source


def menu_marker(kind):
    return '_root.__m002Emit("'+kind+'", escape(v) + "," + escape(_menuEnabled) + "," + escape(_root.game_menu._visible));\n'


INSERTIONS=[state_marker('startfight-entry',True),state_marker('startfight-state-written'),state_marker('startfight-exit',True),menu_marker('menu-write-before'),menu_marker('menu-write-after'),menu_marker('menu-exit')]


def patch_source(source):
    if source.count(START)!=1 or source.count(MENU)!=1:raise ValueError('Missing or ambiguous exact startFight/menu body')
    if any(kind in source for kind in ['startfight-entry','menu-write-before']):raise ValueError('Marker collision')
    start=START.replace('{\r\n','{\r\n'+INSERTIONS[0],1)
    start=start.replace('   _root.setMenuEnable(true);',INSERTIONS[1]+'   _root.setMenuEnable(true);',1)
    start=start[:-1]+INSERTIONS[2]+'}'
    menu=MENU.replace('   _menuEnabled = v;',INSERTIONS[3]+'   _menuEnabled = v;\n'+INSERTIONS[4],1)
    menu=menu[:-1]+INSERTIONS[5]+'}'
    return source.replace(START,start,1).replace(MENU,menu,1)


def build(jar,output,run_id):
    r08.build(jar,output,run_id)
    base=r08.r07.base
    report=json.loads((output/'build.json').read_text())
    (output/'r08-build.json').write_text(json.dumps(report,indent=2)+'\n')
    inherited=r08.patch_sources(r08.r07.sources('scripts/main.json'),run_id)[FRAME]
    patched=patch_source(inherited)
    patch=output/'startfight';target=patch/'scripts'/FRAME;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(patched)
    movie=output/'game/main.swf';before=output/'r08-main.swf';shutil.copyfile(movie,before)
    command=['java','-Djava.awt.headless=true','-jar',str(jar),'-importScript',str(before),str(movie),str(patch)]
    run=subprocess.run(command,capture_output=True)
    (output/'startfight.stdout').write_bytes(run.stdout);(output/'startfight.stderr').write_bytes(run.stderr)
    if run.returncode:raise ValueError('startFight compile failed')
    a,b=base.tags(before),base.tags(movie)
    if a.keys()!=b.keys() or [k for k in a if a[k]!=b[k]]!=['root/637:12']:raise ValueError('Unexpected startFight tag changes')
    original=base.tags(ROOT/'game/main.swf')
    if [k for k in original if original[k]!=b[k]]!=report['changed_tag_paths_by_asset']['game/main.swf']:raise ValueError('Original tag audit changed scope')
    report['outputs_sha256']['game/main.swf']=base.sha(movie)
    for name,digest in report['outputs_sha256'].items():
        if base.sha(output/name)!=digest:raise ValueError('Unexpected output mutation')
    diff=''.join(difflib.unified_diff(inherited.splitlines(True),patched.splitlines(True),fromfile=FRAME+'.r08',tofile=FRAME+'.r12'))
    (output/'startfight.diff.gz').write_bytes(gzip.compress(diff.encode(),mtime=0))
    report.update(facility='r12',startfight_builder_sha256=base.sha(Path(__file__)),parent_r08_sha256=base.sha(output/'r08-build.json'),
                  startfight_diff_sha256=base.sha(output/'startfight.diff.gz'),startfight_command=command,
                  production_admitted=False,native_parity_proven=False,oracle_accepted=False,live_validated=False)
    (output/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['changed_tag_paths_by_asset']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ffdec',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--run-id',required=True)
    a=p.parse_args();build(a.ffdec.resolve(),a.output.resolve(),a.run_id)
