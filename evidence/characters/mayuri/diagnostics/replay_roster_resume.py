import gzip,hashlib,json,os,shutil,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
sys.path[:0]=['tools','tools/probes']
from test_move_cases import validate_timer_contract,target_seen
from compare_mode_reference import compare
root=Path.cwd();tmp=Path('/private/tmp/bvn-mayuri-port');prior=tmp/'regressions-r04/flash-replay';out=tmp/'regressions-final/flash-replay';out.mkdir(parents=True,exist_ok=True)
godot='/Users/fengkx/me/agent-code/toolchains/godot-4.7.2/Godot.app/Contents/MacOS/Godot'
index=json.loads(Path('evidence/characters/itachi/review-mediums/regressions.json').read_text())
assert index['cases']==len(index['results'])==103
assert len(index['fighters'])==16
for fighter in ['orochimaru','jiraiya','pain','konan','daitu','didala','lanran','jianba','gaara']:
 for row in json.loads(Path(f'evidence/characters/{fighter}/comparisons.json').read_text()):
  index['results'].append({'id':row['id'],'fixture':row['paths']['fixture'],'source':row['paths']['source'],'hashes':row['hashes']})
assert len(index['results'])==204
for c in index['results']:
 assert hashlib.sha256(Path(c['fixture']).read_bytes()).hexdigest()==c['hashes']['fixture']
 assert hashlib.sha256(gzip.decompress(Path(c['source']).read_bytes())).hexdigest()==c['hashes']['source']
matched={line.removesuffix(' matched') for line in (tmp/'roster-r04.log').read_text().splitlines() if line.endswith(' matched')}
def replay(case):
 folder=out/case['id'];folder.mkdir(exist_ok=True);fixture=(root/case['fixture']).resolve();spec=json.loads(fixture.read_text());validate_timer_contract(spec);native=folder/(fixture.stem+'.json');started=time.monotonic();timed_out=False
 old=prior/case['id'];reused=case['id'] in matched
 if reused:
  shutil.copy2(old/native.name,native);log=(old/'process.log').read_text();code=0
  shutil.copy2(old/'engine.log',folder/'engine.log')
 else:
  cmd=[godot,'--headless','--path',str(root/'godot'),'--log-file',str(folder/'engine.log'),'-s','res://tests/move_case_reference.gd','--quit-after','1200','--',str(fixture),str(native)]
  try:
   run=subprocess.run(cmd,capture_output=True,text=True,timeout=600);log=run.stdout+run.stderr;code=run.returncode
  except subprocess.TimeoutExpired as e:
   def text(v):return v.decode(errors='replace') if isinstance(v,bytes) else (v or '')
   log=text(e.stdout)+text(e.stderr);code=-1;timed_out=True
 (folder/'process.log').write_text(log);rows=json.loads(native.read_text()) if native.exists() and not timed_out else []
 executed=code==0 and 'MOVE_CASE_REFERENCE_OK' in log and 'SCRIPT ERROR' not in log and len(rows)==2*(spec['frames']+1)
 result={'id':case['id'],'execution':{'executed':executed,'exit':code,'timed_out':timed_out,'states':len(rows),'target_seen':target_seen(spec,rows)},'comparison':compare(root/case['source'],native) if executed else None,'reused_completed_r04':reused,'seconds':None if reused else time.monotonic()-started}
 print(case['id'],result['comparison']['status'] if result['comparison'] else result['execution'],'reused' if reused else 'executed',flush=True)
 return result
started=time.monotonic();results=[]
with ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(replay,c) for c in index['results']]
 for future in as_completed(futures):
  results.append(future.result());(out/'report.json').write_text(json.dumps({'status':'running','workers':2,'seconds':time.monotonic()-started,'results':results},indent=2))
assert len(results)==204
ok=all(r['execution']['executed'] and r['comparison']['status']=='matched' for r in results)
report={'status':'matched' if ok else 'failed','workers':2,'seconds':time.monotonic()-started,'reused_completed_cases':sum(r['reused_completed_r04'] for r in results),'results':results}
(out/'report.json').write_text(json.dumps(report,indent=2));assert ok
assert sum(r['comparison']['source_states'] for r in results)==119008
print('FLASH_REPLAY_OK cases=204 primary_fighters=24 states=119008',report['seconds'])
