"""Revalidate retained bytes without executing Godot or changing old evidence."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]

def main():
    results = {}
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        for label, tape, replay, acceptance in (
            ('r13', 'input-binary-r13', 'replay-ready-report/replay.json.gz', 'replay-ready-report/acceptance.json.gz'),
            ('r12', 'input-alias-r12', 'replay-ready-report/r12.json.gz', 'replay-runtime-cleanup/bvn-runtime-r12-after-acceptance.json.gz'),
        ):
            replay_path = ROOT / 'evidence/oracle' / replay
            (tmp/'replay.json').write_bytes(gzip.decompress(replay_path.read_bytes()))
            run = subprocess.run([sys.executable, str(ROOT/'tools/probes/validate_ai_continuous_replay.py'),
                str(ROOT/'evidence/ai'/tape/'events.jsonl'), str(tmp/'replay.json'), '--horizon', '600',
                '--output', str(tmp/'acceptance.json')], capture_output=True, text=True)
            actual = json.loads((tmp/'acceptance.json').read_text())
            retained = json.loads(gzip.decompress((ROOT/'evidence/oracle'/acceptance).read_bytes()))
            for key in ('checks', 'source_build_provenance', 'first_reason'):
                assert actual[key] == retained[key], (label, key)
            assert run.returncode == 1 and actual['first_reason'] == 'source_build_provenance_not_clean'
            results[label] = {'exit': run.returncode, 'checks_equal': True, 'provenance_equal': True,
                'first_reason': actual['first_reason'], 'replay_sha256': hashlib.sha256(replay_path.read_bytes()).hexdigest()}
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
