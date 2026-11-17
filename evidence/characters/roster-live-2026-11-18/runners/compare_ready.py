from pathlib import Path
import json,sys
sys.path.insert(0,'tools/probes')
from compare_mode_reference import compare, compare_root_position
r=Path('/private/tmp/bvn-roster-live');out=r/'comparisons';out.mkdir(exist_ok=True);results=[]
for entry in json.loads((r/'native-r02/execution.json').read_text()):
 slug=entry['id'];events=r/'original'/slug/'collected/events.jsonl'
 if not events.exists():continue
 folder=r/'native-r02'/slug
 if entry['method']=='terminal-replay':folder=folder/'terminal-replay'
 result=compare(events,folder/'state-420.json')
 result['root_position']=compare_root_position(events,folder/'state-420.json.presentation.json')
 (out/(slug+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 results.append({'id':slug,**{k:result[k] for k in ('status','source_states','native_states','complete')},'differences':len(result['differences'])})
(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
