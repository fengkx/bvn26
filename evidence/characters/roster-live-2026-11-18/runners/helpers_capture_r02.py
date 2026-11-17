from pathlib import Path
import json,subprocess,sys,time
r=Path('/private/tmp/bvn-roster-live');out=r/'helper-original';results=[]
cases=sorted((r/'helper-cases').glob('*.json'),key=lambda p:(0 if p.stem.startswith(('minrenx-','yihu-2-')) else 1,p.name))
while not (r/'original/execution.json').exists() or len(json.loads((r/'original/execution.json').read_text())) < 40:
 time.sleep(5)
for case in cases:
 c=json.loads(case.read_text());folder=out/c['id']
 while True:
  try:
   if any(x['id']==c['id'] for x in json.loads((r/'helper-native/execution.json').read_text())):break
  except FileNotFoundError:pass
  time.sleep(5)
 if (folder/'collected/summary.json').exists():results.append({'id':c['id'],'reused':True});continue
 start=time.monotonic()
 for label,args in [('capture',['tools/probes/capture_native_player.py',str(folder/'probe'),str(folder/'original.log'),'--allow-window-activation','--timeout','300','--lock-timeout','600']),('collect',['tools/probes/collect_ai_reference.py','--build',str(folder/'probe'),'--capture',str(folder/'original.log'),'--output',str(folder/'collected'),'--retain-post-done-frames'])]:
  with (folder/(label+'.log')).open('w') as log:p=subprocess.run([sys.executable,*args],stdout=log,stderr=subprocess.STDOUT,timeout=960)
  if p.returncode:raise RuntimeError((label,c['id'],p.returncode))
 results.append({'id':c['id'],'seconds':time.monotonic()-start});(out/'execution.json').write_text(json.dumps(results,indent=2)+'\n');print('captured',c['id'],flush=True)
(out/'execution.json').write_text(json.dumps(results,indent=2)+'\n')
