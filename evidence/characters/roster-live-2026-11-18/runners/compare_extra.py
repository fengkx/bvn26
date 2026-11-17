from pathlib import Path
import json,sys
sys.path.insert(0,'tools/probes')
from compare_mode_reference import compare,compare_root_position,validate_probe_provenance
r=Path('/private/tmp/bvn-roster-live')
for category in ['break','curved']:
 out=r/(category+'-comparisons');out.mkdir(exist_ok=True);results=[]
 for src in sorted((r/(category+'-original')).iterdir()):
  if not src.is_dir() or not (src/'collected/summary.json').exists():continue
  native=r/(category+'-native')/src.name
  if category=='curved':native=r/'curved-native'
  events=src/'collected/events.jsonl';result=compare(events,native/'state-420.json');result['root_position']=compare_root_position(events,native/'state-420.json.presentation.json');result['provenance']=validate_probe_provenance(events)
  result['guard_packets']=[{'tick':x['fight_tick'],'value':x['value']} for x in map(json.loads,events.read_text().splitlines()) if x['kind']=='source_guard_packet']
  (out/(src.name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
  results.append({'id':src.name,'actors':result['status'],'root':result['root_position']['status'],'guard_packets':result['guard_packets']})
 (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n');print(category,len(results),results[-1:] )
