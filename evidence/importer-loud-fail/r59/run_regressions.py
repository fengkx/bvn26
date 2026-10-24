import subprocess,json,pathlib
out=pathlib.Path('/tmp/bvn-r59/regressions');godot='/tmp/bvn-loud-fail/r02/engine/Godot.app/Contents/MacOS/Godot'
commands={
'r36':['tools/probes/run_normal_composition.py','--godot',godot,'--native','evidence/importer-loud-fail/r36','--output',str(out/'r36')],
'r37':['tools/probes/run_nested_composition.py','--godot',godot,'--native','evidence/importer-loud-fail/r37/native','--output',str(out/'r37')],
'leaf':['tools/probes/run_bound_bitmap_component.py','--build','evidence/importer-loud-fail/r33/native','--godot',godot,'--output',str(out/'leaf')],
'glow':['tools/probes/run_yulong_wrapper.py','--godot',godot,'--output',str(out/'glow')],
'sampler':['tools/probes/run_bitmap_godot_fixture.py','--godot',godot,'--output',str(out/'sampler')],
'cpu':['tools/probes/analyze_bitmap_repeat_spans.py','--output',str(out/'cpu.json')],
}
summary={}
for name,cmd in commands.items():
 p=subprocess.run(['python3',*cmd],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (out/(name+'.log')).write_text(p.stdout);summary[name]=p.returncode
 print(name,p.returncode,flush=True)
(out/'exits.json').write_text(json.dumps(summary,indent=2)+'\n')
