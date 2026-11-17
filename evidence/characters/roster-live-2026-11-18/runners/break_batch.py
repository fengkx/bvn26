from pathlib import Path
import subprocess,json,time,sys
r=Path('/private/tmp/bvn-roster-live');out=r/'break-native';out.mkdir(exist_ok=True);results=[]
while not (r/'helper-original/execution.json').exists() or len(json.loads((r/'helper-original/execution.json').read_text()))<6:time.sleep(5)
for c in sorted((r/'break-cases').glob('*.json')):
 slug=c.stem;native=out/slug;native.mkdir(exist_ok=True);src=r/'break-original'/slug
 while not (src/'probe/build.json').exists():time.sleep(5)
 start=time.monotonic()
 jobs=[('native',native/'run.log',['/Users/fengkx/me/agent-code/toolchains/godot-4.7.2/Godot.app/Contents/MacOS/Godot','--path',str(Path('godot').resolve()),'-s',str(r/'checkpoint_visual.gd'),'--quit-after','10000','--',str(c),str(native)]),('capture',src/'capture.log',[sys.executable,'tools/probes/capture_native_player.py',str(src/'probe'),str(src/'original.log'),'--allow-window-activation','--timeout','180']),('collect',src/'collect.log',[sys.executable,'tools/probes/collect_ai_reference.py','--build',str(src/'probe'),'--capture',str(src/'original.log'),'--output',str(src/'collected'),'--retain-post-done-frames'])]
 for kind,log,args in jobs:
  with log.open('w') as f:p=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=240)
  if p.returncode:raise RuntimeError((slug,kind,p.returncode))
  if kind=='native':
   txt=log.read_text();assert 'ROSTER_CHECKPOINT_VISUAL_OK' in txt and 'SCRIPT ERROR' not in txt and 'leaked' not in txt
 results.append({'id':slug,'seconds':time.monotonic()-start,'passed':True});(out/'execution.json').write_text(json.dumps(results,indent=2)+'\n');print('break captured',slug,flush=True)
