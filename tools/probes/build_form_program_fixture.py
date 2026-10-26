"""Rebuild source-bound controller/BODY fixtures without duplicating production assets."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from build_form_profile import compile_programs


def build(fighter, output):
    timeline = json.loads((ROOT / 'godot/generated/fighters' / fighter / 'timeline.json').read_text())
    source = timeline['source_swf']['path']
    bundle = json.loads((ROOT / source.replace('game/', 'scripts/', 1).replace('.swf', '.json')).read_text())
    if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != timeline['source_swf']['sha256']:
        raise ValueError(f'{source}: stale fixture source hash')
    output.mkdir(parents=True, exist_ok=False)
    compile_programs(output, bundle, timeline)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fighter', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    build(args.fighter, args.output)
