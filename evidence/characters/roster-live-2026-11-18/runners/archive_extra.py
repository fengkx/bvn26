from pathlib import Path
import json,tarfile,hashlib
r=Path('/private/tmp/bvn-roster-live');e=Path('evidence/characters/roster-live-2026-11-18')
for category in ['helper','break','curved']:
 out=e/(category+'-captures');out.mkdir(exist_ok=True);results=[]
 for src in sorted((r/(category+'-original')).iterdir()):
  if not src.is_dir() or not (src/'collected/summary.json').exists():continue
  if not (r/(category+'-comparisons')/(src.name+'.json')).exists():continue
  native=r/(category+'-native')/src.name
  if category=='curved':native=r/'curved-native'
  dest=out/(src.name+'.tar.gz')
  if not dest.exists():
   with tarfile.open(dest,'w:gz',compresslevel=6) as t:
    t.add(r/(category+'-cases')/(src.name+'.json'),arcname='case.json')
    for p in native.iterdir():
     if p.is_file() and p.suffix in ['.png','.json','.log']:t.add(p,arcname='native/'+p.name)
    for name in ['original.log','capture.log','capture-environment.json','collect.log','build.log']:
     if (src/name).exists():t.add(src/name,arcname='original/'+name)
    for p in (src/'collected').iterdir():
     if p.is_file():t.add(p,arcname='original/collected/'+p.name)
   print('archived',category,src.name,flush=True)
  result=json.loads((r/(category+'-comparisons')/(src.name+'.json')).read_text())
  results.append({'id':src.name,'capture':str(dest.relative_to(e)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'comparison':result})
 (e/(category+'-comparison.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
