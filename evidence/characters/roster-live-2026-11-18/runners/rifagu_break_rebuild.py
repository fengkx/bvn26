from pathlib import Path
import json,subprocess,sys,time
r=Path('/private/tmp/bvn-roster-live');out=r/'break-original';out.mkdir(exist_ok=True);catalog=json.load(open('manifest.json'))['fighter_catalog'];built=[];captured=[]
cases=[r/'break-cases/rifagu-break-live.json']
for case in cases:
 c=json.loads(case.read_text());folder=out/c['id'];folder.mkdir(exist_ok=True)
 selected={slot:next(name for name,v in catalog.items() if Path(v.get('url','')).stem.lower()==slug and int(v.get('WKframe',1))==int(c['selected_forms'].get(slot,1))) for slot,slug in c['fighters'].items()}
 args=['tools/probes/build_ai_reference.py','--ffdec','/Users/fengkx/me/agent-code/toolchains/jpexs-26.2.1/ffdec.jar','--output',str(folder/'probe'),'--run-id',c['id']+'-r02','--frames',str(c['frames']),'--p1-character',selected['p1'],'--p2-character',selected['p2'],'--p1-helper',c['p1_helper'],'--p2-helper',c['p2_helper'],'--move-case',str(case),'--sampling-bitmap','--presentation-probe','--hit-receive-probe','--profile','diagnostic','--diagnostic-auto-start','--diagnostic-key-injection','--diagnostic-trace-hooks']
 start=time.monotonic()
 if (folder/'probe/build.json').exists():
  built.append({'id':c['id'],'reused':True});continue
 with (folder/'build.log').open('w') as log:p=subprocess.run([sys.executable,*args],stdout=log,stderr=subprocess.STDOUT,timeout=240)
 if p.returncode:raise RuntimeError(('build',c['id'],p.returncode))
 meta=json.loads((folder/'probe/build.json').read_text());assert meta['sampling_bitmap_ticks']==c['bitmap_ticks']
 built.append({'id':c['id'],'seconds':time.monotonic()-start});(out/'built.json').write_text(json.dumps(built,indent=2)+'\n');print('built',c['id'],flush=True)
