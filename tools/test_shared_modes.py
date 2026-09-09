"""Run both local-input modes against their complete source state windows."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent / 'probes'))
from compare_mode_reference import compare

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bvn-shared-modes-') as directory:
        for mode, name in [(3, 'pvp'), (4, 'training-timer')]:
            output = Path(directory) / f'{mode}.json'
            events = ROOT / 'evidence/combat/shared-mode-validation' / name / 'events.jsonl'
            result = subprocess.run([args.godot, '--headless', '--path', str(ROOT / 'godot'),
                '--log-file', str(Path(directory) / f'{mode}.engine'), '--quit-after', '900',
                '-s', 'res://tests/mode_combat_reference.gd', '--', str(mode), str(output), str(events)],
                capture_output=True, text=True, timeout=90, check=True)
            if 'SCRIPT ERROR' in result.stdout + result.stderr or 'MODE_COMBAT_REFERENCE_OK' not in result.stdout:
                raise RuntimeError(result.stdout + result.stderr)
            comparison = compare(events, output)
            if comparison['status'] != 'matched':
                raise AssertionError(json.dumps(comparison))
            print(f'SHARED_MODE_MATCH {name}: {comparison["source_states"]} actor states', flush=True)


if __name__ == '__main__':
    main()
