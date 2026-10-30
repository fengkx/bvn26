"""Create an analysis-only paired scene runner outside the production tree."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def build(source):
    replacements = [
        ('\tgame.recorded_training_timers = true', '\tgame.recorded_training_timers = true\n\tgame.ko_recorded_timers = true'),
        ('\t_capture_geometry(tick)', '\t_capture_geometry(tick)\n\t_s262_observe(tick)'),
        ('\tquit(2 if failed else 0)', '\t_s262_finish()'),
    ]
    for before, after in replacements:
        if source.count(before) != 1:
            raise ValueError('case runner boundary changed: ' + before)
        source = source.replace(before, after)
    # Disable the image and batch entrypoints: this runner is a pre-image rejection gate.
    source = source.replace('if args[0] == "--bitmap-sequence":', 'if false:')
    source = source.replace('elif args[0] == "--batch":', 'elif false:')
    return source + '\n' + (HERE / 'scene_checks.gd').read_text()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source = ROOT / 'godot/tests/move_case_reference.gd'
    args.output.write_text(build(source.read_text()))
    print(json.dumps({'source': str(source.relative_to(ROOT)),
                      'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                      'runner_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
