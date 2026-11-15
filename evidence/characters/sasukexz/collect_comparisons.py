"""Bind every accepted actor-state comparison to its input and both raw traces."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/probes'))
from compare_mode_reference import compare, source_rows


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sets = [('cases', 'native-r01'), ('interaction-cases', 'native-interaction-r01'),
        ('negative-cases', 'native-negative-r01'), ('lifecycle-cases', 'native-lifecycle-r01'),
        ('followup-cases-r02', 'native-followup-r02')]
results = []
for fixtures, natives in sets:
    for fixture in sorted((OUT / fixtures).glob('*.json')):
        case = json.loads(fixture.read_text())
        if case['id'] == 'sasukexz-repeat-followup':
            continue
        capture = 'original-upper-r01' if case['id'] == 'sasukexz-upper-attack' else 'original-batch-r01'
        source = OUT / capture / case['id'] / 'events.jsonl'
        build = OUT / capture / ('build-' + case['id']) / 'build.json'
        native = OUT / natives / (case['id'] + '.json')
        comparison = compare(source, native)
        rows = source_rows(source)
        low, high = case['target_frames']
        target = any(r['slot'] == case['slot'] and low <= r['frame'] <= high for r in rows)
        result = {'id':case['id'], 'comparison':comparison, 'source_target_seen':target,
                  'paths':{k:str(p.relative_to(ROOT)) for k,p in [('fixture',fixture),('source',source),('native',native),('build',build)]},
                  'hashes':{k:sha(p) for k,p in [('fixture',fixture),('source',source),('native',native),('build',build)]}}
        if 'repeat-' in case['id']:
            frame = 489 if 'warp' in case['id'] else 637
            entries=[]
            previous=None
            for row in rows:
                if row['slot'] != 'p1': continue
                if row['frame']==frame and previous!=frame:
                    opponent=next(r for r in rows if r['tick']==row['tick'] and r['slot']=='p2')
                    entries.append({'tick':row['tick'],'actor_x':row['x'],'opponent_x':opponent['x'],'facing':row['xscale']})
                previous=row['frame']
            result['continuous_entries']=entries
        results.append(result)
(OUT / 'comparisons.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
assert len(results)==19
assert all(r['comparison']['status']=='matched' and r['source_target_seen'] for r in results)
print(json.dumps({'cases':len(results),'states':sum(r['comparison']['source_states'] for r in results),'fields':14,'status':'targeted_actor_states_matched','full_parity':False}))
