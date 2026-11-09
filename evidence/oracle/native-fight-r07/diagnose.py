"""Offline r06/source cross-check; no native process or input operations."""
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
R06=HERE.parent/'native-fight-r06'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def source(name):return {s['path']:s['source'] for s in json.loads((ROOT/name).read_text())['scripts']}


def diagnose():
    manifest=json.loads((ROOT/'manifest.json').read_text())['file_sha256']
    names=['scripts/main.json','scripts/fighter/yihu.json','scripts/fighter/ichigo.json','game/main.swf','game/fighter/yihu.swf','game/fighter/ichigo.swf']
    for name in names:
        if sha(ROOT/name)!=manifest[name]:raise ValueError('Locked input mismatch: '+name)
    build=json.loads((R06/'build.json').read_text())
    session=json.loads((R06/'run-01/session.json').read_text())
    if session['observer_build']!=build:raise ValueError('Build receipt mismatch')
    checks={}
    for name in ['game/main.swf','game/fighter/ichigo.swf','game/fighter/yihu.swf']:
        path=Path(session['build']['path'])/name
        checks[name]=dict(original_sha256=manifest[name],captured_copy_sha256=build['outputs_sha256'][name],retained_copy_matches=sha(path)==build['outputs_sha256'][name] if path.exists() else None)
    spec=importlib.util.spec_from_file_location('r03_parse',HERE.parent/'native-fight-r03/analyze.py');parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
    rows=parser.parse((R06/'run-01/tagged.log').read_bytes(),build['run_id'])
    main=source('scripts/main.json');fighter=source('scripts/fighter/yihu.json')
    registry=[line for line in main['frame_6/DoAction.as'].splitlines() if 'addFighterData("一护",' in line or 'addFighterClone("一护2",' in line]
    if len(registry)!=2 or 'url:"yihu.swf"' not in registry[0] or 'url:"ichigo.swf"' not in registry[1]:raise ValueError('Registry binding changed')
    states=[r for r in rows if r['kind']=='game-state']
    if {unquote(r['data'].split(',')[7]) for r in states}!={'一护'}:raise ValueError('Selected identity mismatch')
    boundary=[]
    for i,row in enumerate(rows):
        if row['kind'] in ('clock-entry','clock-exit'):
            actors=rows[i+1:i+3]
            unknown=[dict(seq=a['seq'],slot=unquote(a['data'].split(',')[0]),field_index=j,value=unquote(v)) for a in actors for j,v in enumerate(a['data'].split(',')) if unquote(v)=='undefined']
            if unknown:boundary.append(dict(seq=row['seq'],local_timer=row['data'].split(',')[0],unknown=unknown))
    init=main['frame_8/DoAction.as'];lines=init.splitlines();hp_line=next(i for i,l in enumerate(lines,1) if '_root.game.p1.mc.hp = _root.game.p2.mc.hp = _root.maxhp;' in l)
    report=dict(production_admitted=False,native_parity_proven=False,oracle_accepted=False,
      source_hashes={n:manifest[n] for n in names},r06_hashes={n:sha(R06/n) for n in ['build.json','run-01/session.json','run-01/tagged.log','run-01/flashlog.after.log','run-01/08-fight-j.jpg']},
      registry=registry,selected_p1='一护',source_selected_asset='game/fighter/yihu.swf',r05_instrumented_asset='game/fighter/ichigo.swf',copies=checks,
      loadman_source=main['DefineSprite_1900/frame_1/DoAction.as'].split('function loadman(pr)',1)[1].split('function loadfz',1)[0],
      decision_lifecycle=dict(path='scripts/fighter/yihu.json:DefineSprite_638/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as',source=fighter['DefineSprite_638/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as']),
      hp_initialization=dict(path='scripts/main.json:frame_8/DoAction.as',line=hp_line,statement=lines[hp_line-1]),
      incomplete_boundaries=boundary,physical_fight_j=session['input_operations'][-1],
      missing=['loaded URL/definition/decision-install identity','native query return at corrected site','HP initialization boundary event ordering versus timer callbacks','certified input tick/global clock','full random tape/repeat/noninterference'])
    (HERE/'diagnosis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    report=diagnose()
    print(json.dumps(dict(selected=report['source_selected_asset'],instrumented=report['r05_instrumented_asset'],incomplete_boundaries=len(report['incomplete_boundaries']))))
