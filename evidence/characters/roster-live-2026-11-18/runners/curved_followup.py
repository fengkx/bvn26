from pathlib import Path
import subprocess,sys,time
r=Path('/private/tmp/bvn-roster-live');src=r/'curved-original/yihu-2-curved-live';out=r/'curved-native';out.mkdir(exist_ok=True)
while not (src/'probe/build.json').exists():time.sleep(2)
jobs=[('capture',[sys.executable,'tools/probes/capture_native_player.py',str(src/'probe'),str(src/'original.log'),'--allow-window-activation','--timeout','300','--lock-timeout','600']),('collect',[sys.executable,'tools/probes/collect_ai_reference.py','--build',str(src/'probe'),'--capture',str(src/'original.log'),'--output',str(src/'collected'),'--retain-post-done-frames']),('native',['/Users/fengkx/me/agent-code/toolchains/godot-4.7.2/Godot.app/Contents/MacOS/Godot','--path',str(Path('godot').resolve()),'-s',str(r/'checkpoint_visual.gd'),'--quit-after','10000','--',str(r/'curved-cases/yihu-2-curved-live.json'),str(out)])]
for kind,args in jobs:
 with (src/(kind+'.log')).open('w') as f:p=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=960)
 if p.returncode:raise RuntimeError((kind,p.returncode))
 print('CURVED_FOLLOWUP',kind,flush=True)
