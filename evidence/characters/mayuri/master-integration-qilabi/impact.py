import json,subprocess,sys,types
from pathlib import Path
sys.path.insert(0,str(Path('tools/importer').resolve()))
import combat_projectile_parser,build_combat_model,compile_ai_controller
names=['combat_projectile_parser','build_combat_model','compile_ai_controller'];current=[sys.modules[n] for n in names]
def load(ref):
 result=[]
 for n in names:
  m=types.ModuleType(n);m.__file__=str(Path('tools/importer',n+'.py').resolve());sys.modules[n]=m;source=subprocess.check_output(['git','show',ref+':tools/importer/'+n+'.py'],text=True);exec(compile(source,m.__file__,'exec'),m.__dict__);result.append(m)
 for n,m in zip(names,current):sys.modules[n]=m
 return result
parents={'mayuri':load('7759d483'),'qilabi':load('117e641f')};rows=[]
for path in sorted(Path('data/slices').glob('*-base.json')):
 role=path.stem[:-5];cached=Path('godot/generated/fighters')/role.lower()
 if not (cached/'combat.json').exists():continue
 old=parents['qilabi' if role=='qilabi' else 'mayuri'];tp=path.with_name(role+'-base.timeline.json');f=json.loads(path.read_text());sp=Path(f['source']['script_bundle_path']);t=json.loads(tp.read_text());b=json.loads(sp.read_text());r={'role':role,'parent':'117e641f' if role=='qilabi' else '7759d483','combat_equal':old[1].build_model(path,tp,sp)==current[1].build_model(path,tp,sp)}
 for player in [True,False]:
  a=old[2].compile_controller(b,t['sprite_id'],t,player=player);c=current[2].compile_controller(b,t['sprite_id'],t,player=player);r['player' if player else 'cpu']={'code_equal':a[0]==c[0],'metadata_equal':a[1]==c[1]}
 rows.append(r);print(r,flush=True);Path('/private/tmp/bvn-mayuri-bee-integration/impact.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(r['combat_equal'] and all(r[k]['code_equal'] and r[k]['metadata_equal'] for k in ['player','cpu']) for r in rows)
