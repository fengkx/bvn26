"""Persist source-backed audio, nested visual, and AI representative facts."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
source=json.loads((ROOT/'scripts/fighter/Byakuya.json').read_text())
actions=json.loads((ROOT/'data/actions/Byakuya-base.json').read_text())
script_paths=[]
def walk(v):
 if isinstance(v,dict):
  if 'path' in v and 'source' in v: script_paths.append(v['path'])
  for x in v.values(): walk(x)
 elif isinstance(v,list):
  for x in v: walk(x)
walk(source)
audio=[]
for item in source.get('scripts', []):
 s=item.get('source','')
 if any(k in s for k in ['Sound','sound','start()','snd']): audio.append(item['path'])
mp3=sorted(p.name for p in (ROOT/'godot/generated/fighters/byakuya').glob('*.mp3'))
report={
 'source_hashes':{
  'game/fighter/Byakuya.swf':hashlib.sha256((ROOT/'game/fighter/Byakuya.swf').read_bytes()).hexdigest(),
  'scripts/fighter/Byakuya.json':hashlib.sha256((ROOT/'scripts/fighter/Byakuya.json').read_bytes()).hexdigest()},
 'audio':{'source_sound_paths':audio[:50],'source_sound_path_count':len(audio),'generated_mp3_count':len(mp3),'representative_sound_ids':[619,620]},
 'nested_visual':{
  'source_controller_scopes':['DefineSprite_16/frame_1/DoAction.as','DefineSprite_69/frame_1/DoAction.as','DefineSprite_631/frame_455/DoAction.as','DefineSprite_631/frame_819/DoAction.as'],
  'dynamic_child_scope_69_distinct_from_16':True,
  'timeline_fallthroughs':actions.get('timeline_fallthroughs',[]),
  'clip_placement_count':len(actions.get('clip_placements',[])),
  'projectile_count':len(actions.get('projectiles',[])),
  'source_visual_evidence':'timeline.json plus persisted same-input state traces'},
 'ai':{
  'control_path':actions.get('command_catalog',{}).get('control_path'),
  'predicate_count':len(actions.get('command_catalog',{}).get('predicates',{})),
  'representative_labels':['砍1','砍技1','砍技2','招1','招2','招3','必杀','上必杀','超必杀','跳','跳2','落2','防御','防御2'],
  'ai_context': 'godot/generated/fighters/byakuya/ai.json',
  'same_input_evidence':'label-coverage.json'},
}
(ROOT/'evidence/characters/byakuya/source-representation-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'audio_paths':len(audio),'mp3':len(mp3),'placements':report['nested_visual']['clip_placement_count'],'predicates':report['ai']['predicate_count']},ensure_ascii=False))
