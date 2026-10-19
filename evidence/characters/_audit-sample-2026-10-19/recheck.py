"""Verify retained audit evidence; this does not launch new Flash or Godot runs."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parents[2]
sys.path.insert(0, str(ROOT / 'tools/probes'))
from compare_mode_reference import compare


def main():
    results = json.loads((AUDIT / 'comparisons.json').read_text())
    failures = []
    counts = {role: 0 for role in ('orochimaru', 'jiraiya', 'pain')}
    for result in results:
        case_id = result['id']
        counts[result['fighter']] += 1
        source = AUDIT / 'traces' / (case_id + '.original.jsonl.gz')
        native = AUDIT / 'traces' / (case_id + '.native.json.gz')
        comparison = compare(source, native)
        if comparison['status'] != 'matched' or comparison['source_states'] != 482:
            failures.append({'id': case_id, 'comparison': comparison})
        contents = {
            'fixture': (ROOT / result['fixture']).read_bytes(),
            'original_events': gzip.decompress(source.read_bytes()),
            'native': gzip.decompress(native.read_bytes()),
        }
        for name, data in contents.items():
            if hashlib.sha256(data).hexdigest() != result['hashes'][name]:
                failures.append({'id': case_id, 'hash_mismatch': name})
        build = json.loads(gzip.decompress(
            (AUDIT / 'source-builds' / (case_id + '.build.json.gz')).read_bytes()))
        environment = json.loads(gzip.decompress(
            (AUDIT / 'source-builds' / (case_id + '.capture-environment.json.gz')).read_bytes()))
        altered_schedule = any(build.get(key) for key in (
            'frame_order_probe', 'recovery_order_probe', 'recovery_walk_first',
            'schedule_probe', 'body_boundaries'))
        if build['move_case'] != json.loads(contents['fixture']) or altered_schedule:
            failures.append({'id': case_id, 'invalid_fixture_or_schedule': True})
        if build['run_id'] != result['run_id'] or not environment['done']:
            failures.append({'id': case_id, 'invalid_capture_identity': True})
    if counts != {'orochimaru': 12, 'jiraiya': 13, 'pain': 15}:
        failures.append({'unexpected_case_counts': counts})
    execution = json.loads((AUDIT / 'execution.json').read_text())
    for name, expected in execution['runtime_and_harness_sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            failures.append({'runtime_or_harness_changed': name})
    print(json.dumps({'retained_evidence_only': True, 'cases': len(results),
                      'counts': counts, 'failures': failures}, ensure_ascii=False))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
