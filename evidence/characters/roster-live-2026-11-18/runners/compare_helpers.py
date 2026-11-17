from pathlib import Path
import json,sys
sys.path.insert(0,'tools/probes')
from compare_mode_reference import compare,compare_root_position
from compare_helper_reference import compare as compare_helper,NATIVE_FIELDS
r=Path('/private/tmp/bvn-roster-live');out=r/'helper-comparisons';out.mkdir(exist_ok=True);results=[]
for native in sorted((r/'helper-native').iterdir()):
 if not native.is_dir():continue
 events=r/'helper-original'/native.name/'collected/events.jsonl'
 if not events.exists():continue
 result=compare(events,native/'state-420.json');result['root_position']=compare_root_position(events,native/'state-420.json.presentation.json')
 raw=json.loads((native/'state-420.json.helpers.json').read_text());projection=out/(native.name+'-projected.json');projection.write_text(json.dumps([{k:x[k] for k in NATIVE_FIELDS} for x in raw]))
 result['helpers']=compare_helper(events,projection)
 (out/(native.name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 results.append({'id':native.name,'actors':result['status'],'root':result['root_position']['status'],'helpers':result['helpers']['status'],'first_difference':result['helpers']['first_difference'],'active':result['helpers']['active_row_counts']})
(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
