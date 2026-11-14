import json,subprocess,sys,time,gzip,hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root/'tools'),str(root/'tools/probes')]
from compare_mode_reference import compare, source_rows
from test_move_cases import target_seen
out=Path('/private/tmp/bvn-mayuri-bee-integration');godot='/Users/fengkx/me/agent-code/toolchains/godot-4.7.2/Godot.app/Contents/MacOS/Godot'
def run(name,args):
 start=time.monotonic();p=subprocess.run([godot,'--headless','--path',str(root/'godot'),'--log-file',str(out/(name+'.engine.log')),*args],capture_output=True,text=True,timeout=600);log=p.stdout+p.stderr;(out/(name+'.log')).write_text(log);assert p.returncode==0 and 'SCRIPT ERROR' not in log,(name,log[-1200:]);return {'id':name,'seconds':time.monotonic()-start,'exit':p.returncode}
def replay(row):
 case=root/row['paths']['fixture'];spec=json.loads(case.read_text());source=root/row['paths']['source'];dest=out/(row['id']+'.json')
 assert hashlib.sha256(case.read_bytes()).hexdigest()==row['hashes']['fixture']
 assert hashlib.sha256(gzip.decompress(source.read_bytes())).hexdigest()==row['hashes']['source']
 fresh=None
 if not dest.exists() or not (out/(row['id']+'.log')).exists():fresh=run(row['id'],['-s','res://tests/move_case_reference.gd','--quit-after','1200','--',str(case),str(dest)])
 log=(out/(row['id']+'.log')).read_text()
 assert 'MOVE_CASE_REFERENCE_OK' in log and 'SCRIPT ERROR' not in log
 if row['id'].startswith('qilabi-'):
  assert dest.stat().st_mtime > (root/'godot/generated/fighters/qilabi/ai_controller/controller.json').stat().st_mtime
 r={'id':row['id'],'seconds':None,'execution':'Reused completed native output from this integration run; per-case duration was not persisted before the batch target assertion failed.'}
 if fresh:r.update(fresh);r['execution']='Executed after correcting target classification'
 r['comparison']=compare(source,dest);r['target_seen']=target_seen(spec,json.loads(dest.read_text()));r['source_target_seen']=target_seen(spec,source_rows(source))
 assert r['comparison']['status']=='matched' and r['target_seen']==r['source_target_seen'],r
 if not r['target_seen']:assert spec['scenario']=='energy_below' and row.get('target_seen') is False
 print(row['id'],'matched',r['target_seen'],flush=True);return r

rows=[]
for role in ['mayuri','karin','qilabi']:rows+=json.loads((root/f'evidence/characters/{role}/comparisons.json').read_text())
with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(replay,rows))
(out/'replays.json').write_text(json.dumps(results,indent=2)+'\n')
checks=[]
for name in ['qilabi_rollback_smoke','mayuri_rollback_smoke','karin_rollback_smoke','karin_projectile_rollback_smoke','mayuri_projectile_smoke','interrupted_super_lock_smoke','ai_projectile_instance_variables_smoke','player_controller_smoke','player_visual_smoke']:
 r=run(name,['-s','res://tests/'+name+'.gd']);assert 'OK' in (out/(name+'.log')).read_text();checks.append(r);(out/'godot.json').write_text(json.dumps(checks,indent=2)+'\n');print(name,'passed',flush=True)
