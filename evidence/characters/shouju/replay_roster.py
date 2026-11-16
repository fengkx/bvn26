"""Replay one retained fixture per saved base fighter without changing its tape."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tools/probes')]
from test_move_cases import execute_batch
from compare_mode_reference import compare

out = ROOT / 'evidence/characters/shouju/saved-roster-r01'
out.mkdir(exist_ok=False)
index = json.loads((ROOT / 'evidence/characters/itachi/review-mediums/regressions.json').read_text())['results']
selected = {}
for row in index:
    fixture = ROOT / row['fixture']
    fighter = json.loads(fixture.read_text())['fighter']
    selected.setdefault(fighter, row)
for fighter in ('orochimaru', 'jiraiya', 'pain', 'konan', 'daitu', 'didala', 'lanran',
                'jianba', 'gaara', 'juggo', 'karin', 'mayuri', 'qilabi', 'kenshin', 'weqal'):
    row = json.loads((ROOT / f'evidence/characters/{fighter}/comparisons.json').read_text())[0]
    selected[fighter] = {'id': row['id'], 'fixture': row['paths']['fixture'],
                         'source': row['paths']['source'], 'hashes': row['hashes']}
rows = list(selected.values())
for row in rows:
    assert hashlib.sha256((ROOT / row['fixture']).read_bytes()).hexdigest() == row['hashes']['fixture']
    raw = (ROOT / row['source']).read_bytes()
    if row['source'].endswith('.gz'):
        raw = gzip.decompress(raw)
    assert hashlib.sha256(raw).hexdigest() == row['hashes']['source']
(out / 'selected.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
executions = execute_batch(Path('/Users/fengkx/me/agent-code/toolchains/godot-4.7.2/Godot.app/Contents/MacOS/Godot'),
                           [ROOT / row['fixture'] for row in rows], out)
results = []
for row, execution in zip(rows, executions):
    comparison = compare(ROOT / row['source'], out / (row['id'] + '.json')) if execution['executed'] else None
    results.append({'id': row['id'], 'execution': execution, 'comparison': comparison})
(out / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
assert all(r['execution']['executed'] and r['comparison']['status'] == 'matched' for r in results)
print('SAVED_ROSTER_TARGETED_OK', len(results))
