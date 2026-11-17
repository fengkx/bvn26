from pathlib import Path
import json,sys,tarfile,hashlib,shutil
sys.path.insert(0,'tools/probes')
from compare_mode_reference import compare,compare_root_position,validate_probe_provenance
r=Path('/private/tmp/bvn-roster-live');e=Path('evidence/characters/roster-live-2026-11-18');out=e/'captures';out.mkdir(exist_ok=True);results=[]
for entry in json.loads((r/'native-r02/execution.json').read_text()):
 slug=entry['id'];original=r/'original'/slug;events=original/'collected/events.jsonl'
 if not (original/'collected/summary.json').exists():continue
 native=r/'native-r02'/slug
 if entry['method']=='terminal-replay':native=native/'terminal-replay'
 result=compare(events,native/'state-420.json');result['root_position']=compare_root_position(events,native/'state-420.json.presentation.json');result['provenance']=validate_probe_provenance(events)
 guard=[]
 for line in events.read_text().splitlines():
  row=json.loads(line)
  if row['kind']=='source_guard_packet':guard.append({'tick':row['fight_tick'],'branch':row['value'].rsplit(',',1)[-1]})
 result['guard_packets']=guard
 dest=out/(slug+'.tar.gz')
 if not dest.exists():
  with tarfile.open(dest,'w:gz',compresslevel=6) as t:
   t.add(r/'cases'/(slug+'.json'),arcname='case.json')
   for p in native.iterdir():
    if p.is_file() and (p.suffix in ['.png','.json','.log']):t.add(p,arcname='native/'+p.name)
   for name in ['original.log','capture.log','capture-environment.json','collect.log','build.log']:
    if (original/name).exists():t.add(original/name,arcname='original/'+name)
   for p in (original/'collected').iterdir():
    if p.is_file():t.add(p,arcname='original/collected/'+p.name)
  print('archived',slug,dest.stat().st_size,flush=True)
 results.append({'id':slug,'capture':str(dest.relative_to(e)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'execution':entry,'comparison':result})
(e/'comparison.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('TOTAL',len(results),'MATCHED',sum(x['comparison']['status']=='matched' for x in results),flush=True)
