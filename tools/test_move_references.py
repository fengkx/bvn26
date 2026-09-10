"""Run fresh native Flash fights and compare every observed state exactly.

The dynamic probe is analysis-only. Its fixed instrumented SWFs are reused;
each run retains its external fixture, build metadata, input tape and trace.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parent / 'probes'))
from move_cases import encode_case
from compare_mode_reference import compare, source_rows, compare_root_position, cancellation_observation

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--cases',type=Path,required=True)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--capture-runner',type=Path,required=True)
    parser.add_argument('--scenario',action='append')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--allow-window-activation', action='store_true',
                        help='Explicitly allow native Flash to raise windows')
    args=parser.parse_args()
    if not args.allow_window_activation:
        parser.error('Flash sampling is disabled: the player can raise windows despite background launch')
    from capture_native_player import preflight
    preflight()
    template=json.loads((args.probe/'build.json').read_text())
    if not template.get('dynamic_move_case'): raise ValueError('Dynamic fixture probe required')
    args.output.mkdir(parents=True,exist_ok=True)
    cases=[json.loads(p.read_text()) for p in sorted(args.cases.glob('*.json'))]
    cases=[c for c in cases if not args.scenario or c['scenario'] in args.scenario]
    if args.limit: cases=cases[:args.limit]
    results=[]
    for index,case in enumerate(cases):
        if 'fighters' in case:
            catalog = json.loads((ROOT / 'manifest.json').read_text())['fighter_catalog']
            for slot, fighter in case['fighters'].items():
                selected = template['configuration'][slot]
                if Path(catalog[selected]['url']).stem != fighter:
                    raise ValueError(f'Fixture/probe fighter mismatch: {slot} {fighter} != {selected}')
        folder=args.output/case['id']
        if folder.exists(): raise ValueError(f'Reference must not be overwritten: {folder}')
        scratch=args.output/('build-'+case['id']);scratch.mkdir()
        run_tag = hashlib.sha256(str(args.output.resolve()).encode()).hexdigest()[:10]
        run_id='moves-'+case['id']+'-'+run_tag
        fixture=encode_case(case,run_id)
        (args.probe/'case.txt').write_text(fixture)
        (scratch/'case.txt').write_text(fixture)
        (scratch/'game').symlink_to((args.probe/'game').resolve(),target_is_directory=True)
        (scratch/'instrumentation.diff').write_bytes((args.probe/'instrumentation.diff').read_bytes())
        build=dict(template,run_id=run_id,move_case=case,fixture_sha256=hashlib.sha256(fixture.encode()).hexdigest())
        (scratch/'build.json').write_text(json.dumps(build,ensure_ascii=False,indent=2)+'\n')
        capture=scratch/'original.log'
        commands=[
            [sys.executable,str(args.capture_runner),str(scratch),str(capture),'--allow-window-activation'],
            [sys.executable,str(ROOT/'tools/probes/collect_ai_reference.py'),'--build',str(scratch),'--capture',str(capture),'--output',str(folder),'--retain-post-done-frames'],
        ]
        failure=None
        for command in commands:
            # Lock waiting is not player execution time. The capture runner starts
            # its own deadline only after acquiring the account-wide log lock.
            timeout = None if command == commands[0] else 150
            run=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
            (scratch/('capture.log' if command==commands[0] else 'collect.log')).write_text(run.stdout+run.stderr)
            if run.returncode:
                failure=run.stdout+run.stderr
                break
        if failure:
            result={'id':case['id'],'status':'capture_failed','detail':failure[-2000:]}
        else:
            (folder/'case.txt').write_text(fixture)
            (folder/'case.json').write_text(json.dumps(case,ensure_ascii=False,indent=2)+'\n')
            native=args.native/(case['id']+'.json')
            (folder/'native.json').write_bytes(native.read_bytes())
            result=compare(folder/'events.jsonl',folder/'native.json')
            if template.get('presentation_probe'):
                presentation = folder / 'native.presentation.json'
                presentation.write_bytes(Path(str(native) + '.presentation.json').read_bytes())
                root_result = compare_root_position(folder/'events.jsonl', presentation)
                (folder/'root-position-comparison.json').write_text(json.dumps(root_result, indent=2)+'\n')
                result['root_position'] = root_result['status']
                if root_result['status'] != 'matched':
                    result['status'] = 'different'
            frames=case['target_frames']
            rows=json.loads(native.read_text())
            result['target_seen']=any(r['slot']==case['slot'] and frames[0] is not None and frames[0]<=r['frame']<=frames[1] for r in rows)
            expected=source_rows(folder/'events.jsonl')
            if 'window_boundary' in case:
                result['cancellation'] = cancellation_observation(expected, case)
                if result['cancellation']['status'] != 'calibrated':
                    result['status'] = 'invalid_calibration'
            result['source_target_seen']=any(r['slot']==case['slot'] and frames[0] is not None and frames[0]<=r['frame']<=frames[1] for r in expected)
            if result['status']=='matched' and not result['source_target_seen'] and case['scenario']!='energy_below' and frames[0] is not None:
                result['status']='unexercised'
            result['id']=case['id']
            (folder/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
            result={k:v for k,v in result.items() if k!='differences'}|{'different_states':len(result['differences'])}
        results.append(result)
        (args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(json.dumps({'progress':f'{index+1}/{len(cases)}',**result}),flush=True)
    raise SystemExit(0 if all(r['status']=='matched' for r in results) else 1)


if __name__=='__main__':main()
