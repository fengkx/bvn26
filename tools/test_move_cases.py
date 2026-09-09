"""Execute fresh-fight move fixtures; execution alone is not original parity."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def execute(godot, case_path, output):
    case=json.loads(case_path.read_text())
    target=output/(case_path.stem+'.json')
    command=[str(godot),'--headless','--path',str(ROOT/'godot'),
             '--log-file',str(output/(case_path.stem+'.engine.log')),
             '-s','res://tests/move_case_reference.gd','--quit-after','1200','--',str(case_path),str(target)]
    try:
        run=subprocess.run(command,capture_output=True,text=True,timeout=45)
    except subprocess.TimeoutExpired:
        return {'id':case['id'],'executed':False,'status':'timeout'}
    log=run.stdout+run.stderr
    (output/(case_path.stem+'.log')).write_text(log)
    rows=json.loads(target.read_text()) if target.exists() else []
    complete=len(rows)==2*(case['frames']+1)
    executed=run.returncode==0 and 'SCRIPT ERROR' not in log and 'MOVE_CASE_REFERENCE_OK' in log and complete
    lo,hi=case['target_frames']
    seen=any(r['slot']==case['slot'] and lo is not None and lo<=r['frame']<=hi for r in rows)
    return {'id':case['id'],'executed':executed,'states':len(rows),'target_seen':seen,
            'status':'native_only_not_parity' if executed else 'failed'}



def execute_batch(godot, paths, output):
    index = output / 'case-paths.json'
    index.write_text(json.dumps([str(p) for p in paths]))
    command = [str(godot), '--headless', '--path', str(ROOT / 'godot'),
               '--log-file', str(output / 'engine.log'), '-s', 'res://tests/move_case_reference.gd',
               '--quit-after', str(max(2400, len(paths) * 60)), '--', '--batch', str(index), str(output)]
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=60 + len(paths) * 10)
        log = run.stdout + run.stderr
        clean = run.returncode == 0 and 'SCRIPT ERROR' not in log and 'MOVE_CASE_BATCH_OK' in log
    except subprocess.TimeoutExpired as error:
        log = str(error)
        clean = False
    (output / 'batch.log').write_text(log)
    results = []
    for path in paths:
        case = json.loads(path.read_text())
        target = output / (case['id'] + '.json')
        rows = json.loads(target.read_text()) if target.exists() else []
        complete = len(rows) == 2 * (case['frames'] + 1)
        lo, hi = case['target_frames']
        seen = any(r['slot'] == case['slot'] and lo is not None and lo <= r['frame'] <= hi for r in rows)
        executed = clean and complete and ('MOVE_CASE_REFERENCE_OK ' + case['id']) in log
        results.append({'id': case['id'], 'executed': executed, 'states': len(rows),
                        'target_seen': seen, 'status': 'native_only_not_parity' if executed else 'failed'})
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot',type=Path,required=True)
    parser.add_argument('--cases',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--jobs',type=int,default=1)
    args=parser.parse_args()
    if args.output.exists(): raise ValueError('Use a fresh output directory')
    args.output.mkdir(parents=True)
    paths = sorted(args.cases.glob('*.json'))
    if args.jobs == 1:
        results = execute_batch(args.godot, paths, args.output)
    else:
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(lambda p: execute(args.godot, p, args.output), paths))
    (args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'cases':len(results),'executed':sum(r['executed'] for r in results),'status':'native_only_not_parity'}))
    raise SystemExit(0 if all(r['executed'] for r in results) else 1)


if __name__=='__main__': main()
