"""Compare native Godot sensor geometry against retained original-player events."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',required=True,type=Path);p.add_argument('--godot',required=True,type=Path);p.add_argument('--output',required=True,type=Path);args=p.parse_args()
    events=[json.loads(x) for x in (args.capture/'events.jsonl').read_text().splitlines()]
    geometry=next(e for e in events if e['kind']=='geometry_frame')
    same=[e for e in events if e['display_tick']==geometry['display_tick']]
    players={}
    for e in same:
        if e['kind']!='state':continue
        fields=e['value'].split(',');name,frame,x,y,scale=fields[:5]
        players[name]={'fighter':{'p1':'minren','p2':'yihu'}[name],'frame':int(frame),'x':float(x),'y':float(y),'facing':int(float(scale)/100)}
    sensors={}
    for e in same:
        if e['kind']!='sensor_bounds':continue
        fields=e['value'].split(',');name=fields[0]
        sensors[name]={'bounds':None if fields[1]=='undefined' else list(map(float,fields[1:5])),
                       'hit':{'true':True,'false':False,'undefined':None}[fields[5]]}
    args.output.mkdir(parents=True,exist_ok=True)
    reference=args.output/'reference.json';actual=args.output/'actual.json'
    reference.write_text(json.dumps({'players':players,'sensors':sensors},ensure_ascii=False,indent=2)+'\n')
    run=subprocess.run([str(args.godot),'--headless','--path',str(ROOT/'godot'),'--log-file',str(args.output/'engine.log'),
                        '--script','res://tests/ai_geometry_reference.gd','--',str(reference.resolve()),str(actual.resolve())],text=True,capture_output=True,timeout=30)
    (args.output/'native.log').write_text(run.stdout+run.stderr)
    if run.returncode or 'SCRIPT ERROR' in run.stderr or 'AI_GEOMETRY_REFERENCE_OK' not in run.stdout:
        raise RuntimeError('Godot geometry fixture failed')
    result=json.loads(actual.read_text())
    differences=[];hits=[]
    for name,expected in sensors.items():
        observed=result[name]
        if observed['hit']!=expected['hit']:hits.append({'sensor':name,'expected':expected['hit'],'actual':observed['hit']})
        if expected['bounds'] is None:
            if observed['bounds'] is not None:differences.append({'sensor':name,'expected':None,'actual':observed['bounds']})
        elif observed['bounds']!=expected['bounds']:
            differences.append({'sensor':name,'expected':expected['bounds'],'actual':observed['bounds'],
                                'delta':[b-a for a,b in zip(expected['bounds'],observed['bounds'])]})
    report={'status':'passed' if not differences and not hits else 'mismatch','original_run':geometry['run_id'],
            'source_display_tick':geometry['display_tick'],'sensors':len(sensors),'hit_differences':hits,'bounds_differences':differences,
            'scope':'one original frame, local getBounds and hitTest against current bdmn; exact comparison, no widened tolerance'}
    (args.output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('bounds_differences','hit_differences')}))
    print(json.dumps({'hit_differences':len(hits),'bounds_differences':len(differences)}))
    if report['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
