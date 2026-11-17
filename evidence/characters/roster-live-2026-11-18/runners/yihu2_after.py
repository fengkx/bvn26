from pathlib import Path
import time,json,subprocess,sys
r=Path('/private/tmp/bvn-roster-live')
while len(json.loads((r/'break-native/execution.json').read_text()))<35:time.sleep(5)
out=r/'curved-native-after';out.mkdir(exist_ok=True)
args=['/Users/fengkx/me/agent-code/toolchains/godot-4.7.2/Godot.app/Contents/MacOS/Godot','--path',str(Path('godot').resolve()),'-s',str(r/'checkpoint_visual.gd'),'--quit-after','10000','--',str(r/'curved-cases/yihu-2-curved-live.json'),str(out)]
with (out/'run.log').open('w') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
assert 'ROSTER_CHECKPOINT_VISUAL_OK' in (out/'run.log').read_text()
sys.path.insert(0,'tools/probes')
from compare_mode_reference import compare,compare_root_position
src=r/'curved-original/yihu-2-curved-live/collected/events.jsonl';result=compare(src,out/'state-420.json');result['root_position']=compare_root_position(src,out/'state-420.json.presentation.json')
(out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
