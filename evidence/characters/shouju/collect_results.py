"""Retain exact comparison inputs and keep diagnostic scope explicit."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tools/probes')]
from compare_mode_reference import compare
from test_move_cases import target_seen

OUT = Path(__file__).resolve().parent
traces = OUT / 'traces'
traces.mkdir(exist_ok=True)
results = []
for fixture in sorted((OUT / 'cases').glob('*.json')):
    case = json.loads(fixture.read_text())
    original = OUT / 'original-r01' / case['id'] / 'events.jsonl'
    native = OUT / 'native-r04' / (fixture.stem + '.json')
    comparison = compare(original, native)
    source_trace = traces / (case['id'] + '.original.jsonl.gz')
    native_trace = traces / (case['id'] + '.native.json.gz')
    source_trace.write_bytes(gzip.compress(original.read_bytes(), mtime=0))
    native_trace.write_bytes(gzip.compress(native.read_bytes(), mtime=0))
    row = {
        'id': case['id'], 'comparison': comparison,
        'kind': 'absent_label_negative' if case['scenario'] == 'missing-form' else 'targeted_action',
        'target_seen': target_seen(case, json.loads(native.read_text())),
        'paths': {k: str(p.relative_to(ROOT)) for k, p in
                  [('fixture', fixture), ('source', source_trace), ('native', native_trace)]},
        'hashes': {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in
                   [('fixture', fixture), ('source', original), ('native', native)]},
        'original_capture_directory': str(original.parent.relative_to(ROOT)),
        'native_run_path': str(native.relative_to(ROOT)),
    }
    results.append(row)
    print(case['id'], comparison['status'], row['target_seen'], flush=True)
(OUT / 'comparisons.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
assert len(results) == 16
assert all(r['comparison']['status'] == 'matched' and r['comparison']['complete'] and r['target_seen'] for r in results)
print('TEMARI_TARGETED_MATCHED', len(results), sum(r['comparison']['source_states'] for r in results))
