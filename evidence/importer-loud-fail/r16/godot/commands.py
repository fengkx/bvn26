import json,subprocess,os
from pathlib import Path
out=Path(os.environ['OUT']) / 'godot';out.mkdir(parents=True, exist_ok=True)
godot=os.environ['GODOT']
cases=[]
for mode in ['large','small','bounds']:
 cases.append(('blur-'+mode,'flash_filters_render',[str(out/(mode+'.json')),mode],False))
cases += [('colors','flash_filter_colors_render',[str(out/'colors.json')],False),('order','flash_filter_colors_render',[str(out/'order.json'),str(Path('tools/probes/flash_filters/color-matrix.json').resolve()),'order'],False),('raster','flash_filter_raster_render',[],False),('blend','flash_blend_modes_render',[],False)]
for name in ['player_controller','player_visual','retained_effect_clocks','clip_placement_once']:
 cases.append((name,name+'_smoke',[],True))
for name in ['parent_frame_state_reference','parent_state_checkpoint','numeric_goto_reference','form_callback_reference','repeating_timeouts_smoke','ai_timeouts_smoke','timeout_checkpoint_smoke','controller_checkpoint_smoke','battle_checkpoint_smoke']:
 cases.append((name,name,[],True))
cases += [(name,name,[],True) for name in ['form_input_activation_smoke','transformation_gate_smoke','form_root_interval_replay_smoke','form_replacement_checkpoint']]
cases += [(name,name,[],True) for name in ['yihu_form_graph_reference','minren_form_replacement_reference','form_wankai_graph_reference','visual_playhead_smoke']]
cases.append(('wrapper_filter_initialization_reference','wrapper_filter_initialization_reference',[],True))
rows=[]
for name,script,args,headless in cases:
 command=[godot,'--path','godot','--headless'] if headless else [godot,'--path','godot','--rendering-method','gl_compatibility']
 command+=['--script','res://tests/'+script+'.gd','--quit-after','1200','--log-file',str(out/(name+'-engine.log'))]
 if args:command+=['--']+args
 with (out/(name+'.log')).open('w') as log:
  result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 text=(out/(name+'.log')).read_text()
 rows.append({'test':name,'exit':result.returncode,'passed':result.returncode==0 and 'ERROR' not in text})
 (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(rows[-1],flush=True)
