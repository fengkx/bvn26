"""Check the retained pre-replacement transformation prefix, not the full move."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/probes'))
from compare_mode_reference import compare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', required=True)
    args = parser.parse_args()
    reference = ROOT / 'evidence/combat/move-boundary-validation/references/yihu-962-wankai-neutral'
    with tempfile.TemporaryDirectory(prefix='bvn-transform-start-') as directory:
        output = Path(directory) / 'native.json'
        run = subprocess.run([args.godot, '--headless', '--path', str(ROOT / 'godot'),
                              '--script', 'res://tests/move_case_reference.gd', '--',
                              str(reference / 'case.json'), str(output)],
                             capture_output=True, text=True, timeout=120)
        log = run.stdout + run.stderr
        if run.returncode or 'SCRIPT ERROR' in log or 'MOVE_CASE_REFERENCE_OK' not in log:
            raise RuntimeError(log)
        result = compare(reference / 'events.jsonl.gz', output)
        # The original first replaces its body at observation 101. That separate
        # lifecycle is explicitly outside this focused start-call regression.
        differences = [row for row in result['differences'] if row['tick'] <= 100]
        if not result['complete'] or result['source_states'] != 602 or differences:
            raise AssertionError(json.dumps(differences[:3]))
        print(json.dumps({'status': 'TRANSFORM_START_REFERENCE_OK', 'prefix_states': 202,
                          'full_move_status': result['status']}))


if __name__ == '__main__':
    main()
