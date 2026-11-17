from pathlib import Path
import json,sys,xml.etree.ElementTree as ET,hashlib
sys.path.insert(0,'tools/importer')
from solid_shape_geometry import solid_fill_polygons,solid_fill_meshes,solid_closed_strokes
from compile_ai_context import compile_context
from form_profile_guard import package_hashes
r=Path('/private/tmp/bvn-roster-live');folder=Path('godot/generated/forms/yihu-2');p=folder/'timeline.json';d=json.loads(p.read_text());root=ET.parse(r/(d['source_swf']['sha256']+'.xml')).getroot();shapes={int(t.get('shapeId')):t for t in root.findall('./tags/item') if t.get('shapeId')};changed=[]
for definition in d['definitions']:
 if not definition.get('solid_fills'):continue
 shape=shapes[definition['character_id']];contours=solid_fill_polygons(shape)
 if contours is not None:definition['solid_fill_polygons']=contours
 else:
  meshes=solid_fill_meshes(shape);assert meshes is not None,definition['character_id'];definition['solid_fill_meshes']=meshes
 strokes=solid_closed_strokes(shape)
 if strokes is not None:definition['solid_closed_strokes']=strokes
 changed.append(definition['character_id'])
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
a=folder/'ai.json';old=json.loads(a.read_text());new=compile_context(json.load(open('scripts/fighter/yihu.json')),d,form_replacement=True)
def strip(v):
 if isinstance(v,dict):return {k:strip(x) for k,x in v.items() if k not in ['solid_fill_polygons','solid_fill_meshes','solid_closed_strokes']}
 if isinstance(v,list):return [strip(x) for x in v]
 return v
assert strip(old)==strip(new),'Fresh AI compilation changes more than paint geometry'
a.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
manifest=Path('godot/generated/fighters/yihu/form_profiles.json')
if manifest.exists():
 m=json.loads(manifest.read_text());m['base_files']=package_hashes(manifest.parent)
 for entry in m['profiles'].values():entry['files']=package_hashes(Path('godot')/entry['directory'].removeprefix('res://'))
 manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 req=Path('tools/importer/frame_call_requirements.json');data=json.loads(req.read_text());key=d['source_swf']['sha256']+':'+str(m['base_sprite_id']);data[key]['form_profile_contract']['manifest_sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest();req.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('REFRESHED_YIHU2_SOLIDS',changed)
