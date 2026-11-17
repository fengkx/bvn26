from pathlib import Path
import json,time,subprocess
r=Path('/private/tmp/bvn-roster-live');out=r/'helper-native';out.mkdir(exist_ok=True);results=[]
cases=sorted((r/'helper-cases').glob('*.json'),key=lambda p:(0 if p.stem.startswith(('minrenx-','yihu-2-')) else 1,p.name))
for c in cases:
 folder=out/c.stem;folder.mkdir(exist_ok=True);start=time.monotonic()
 def run(script,dest):
  with (dest/'run.log').open('w') as log:p=subprocess.run(['/Users/fengkx/me/agent-code/toolchains/godot-4.7.2/Godot.app/Contents/MacOS/Godot','--path',str(Path('godot').resolve()),'--log-file',str(dest/'engine.log'),'-s',str(r/script),'--quit-after','10000','--',str(c),str(dest)],stdout=log,stderr=subprocess.STDOUT,timeout=300)
  text=(dest/'run.log').read_text();return p.returncode,text
 code,text=run('checkpoint_visual.gd',folder)
 good=code==0 and 'ROSTER_CHECKPOINT_VISUAL_OK' in text and not any(w in text for w in ['SCRIPT ERROR','leaked','still in use'])
 method='checkpoint'
 if not good:
  dest=folder/'terminal-replay';dest.mkdir(exist_ok=True);code,text=run('visual.gd',dest);good=code==0 and 'ROSTER_LIVE_VISUAL_OK' in text and not any(w in text for w in ['SCRIPT ERROR','leaked','still in use']);method='terminal-replay'
 result={'id':c.stem,'seconds':time.monotonic()-start,'exit':code,'passed':good,'method':method};results.append(result);(out/'execution.json').write_text(json.dumps(results,indent=2)+'\n');print(result,flush=True)
