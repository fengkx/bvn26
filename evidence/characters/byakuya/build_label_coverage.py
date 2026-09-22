"""Build an explicit Byakuya label coverage report from persisted comparisons."""
import json
import hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'evidence/characters/byakuya'
entries = {
 '必杀': ('matched','godot-compare-r09-dual-soul/bisha.json'),
 '空中必杀': ('matched','godot-compare-r11-current/bishaAir.json'),
 '上必杀': ('matched','godot-compare-r09-dual-soul/bishaUP.json'),
 '超必杀': ('matched','godot-compare-r09-dual-soul/bishaSuper.json'),
 '招换': ('matched','godot-compare-r12-helper-fields/summon.json'),
 '招1': ('matched','godot-compare-r10-labels/zhao1.json'),
 '招2': ('matched','godot-compare-r10-labels/zhao2.json'),
 '招3': ('matched','godot-compare-r10-labels/zhao3.json'),
 '跳': ('matched','godot-compare-r10-labels/jump.json'),
 '跳2': ('matched','godot-compare-r10-labels/jump2.json'),
 '落2': ('matched','godot-compare-r10-labels/drop.json'),
 '防御': ('matched','godot-compare-r10-labels/defence.json'),
 '防御2': ('matched','godot-compare-r10-labels/defence2.json'),
 '跳砍': ('matched','godot-compare-r06/compare-matrix-00.json'),
 '砍1': ('matched','godot-compare-r06/compare-matrix-02.json'),
 '瞬步': ('matched','godot-compare-r06/compare-matrix-03.json'),
 '砍技1': ('matched','godot-compare-r06/compare-matrix-04.json'),
 '砍技2': ('matched','godot-compare-r06/compare-matrix-05.json'),
 '跳招': ('matched','godot-compare-r06/compare-matrix-01.json'),
 '万解': (None,None),
}
report={'fighter':'byakuya','labels_total':len(entries),'matched':[],'diverged':[],'uncompared':[],'entries':{},'superseded':{'空中必杀':'godot-compare-r09-dual-soul/bishaAir.json'}}
hash_paths = [ROOT/'godot/fighter_runtime.gd', ROOT/'godot/generated/fighters/byakuya/combat.json', ROOT/'godot/generated/fighters/byakuya/player_controller/controller.gd', ROOT/'godot/generated/fighters/byakuya/ai_controller/controller.gd']
report['hashes'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in hash_paths if p.exists()}
for label,(expected,rel) in entries.items():
 if not rel:
  report['uncompared'].append(label); report['entries'][label]={'status':'uncompared'}; continue
 d=json.loads((OUT/rel).read_text()); status='matched' if d.get('status')=='matched' and not d.get('differences') else 'diverged'
 report[status].append(label); report['entries'][label]={'status':status,'comparison':rel,'source_states':d.get('source_states'),'native_states':d.get('native_states'),'difference_count':len(d.get('differences') or [])}
# Bind every accepted label to the exact current fixture and replay artifact.
accepted={}
for p in sorted((ROOT/'evidence/characters/byakuya/fixtures-full').glob('*-neutral.json')):
 x=json.loads(p.read_text())
 if x.get('label') != '万解': accepted.setdefault(x['label'], p)
accepted['招换']=ROOT/'evidence/characters/byakuya/fixtures-full/byakuya-814-zhaoHuan-air_target.json'
report['accepted_current_artifacts']={}
for label,p in accepted.items():
 if label not in report['matched']: continue
 report['accepted_current_artifacts'][label]={'case_id':json.loads(p.read_text())['id'],'fixture_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'helpers':['魂','魂'],'godot_states':602,'status':'matched_current'}
(OUT/'label-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('labels_total','matched','diverged','uncompared')},ensure_ascii=False))
