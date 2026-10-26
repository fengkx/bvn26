"""Rerun the pinned independent rendering gates without modifying production admission."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def run(godot, output):
    output.mkdir(parents=True, exist_ok=True)
    commands = {
        'r36': ['tools/probes/run_normal_composition.py', '--godot', str(godot), '--native',
                'evidence/importer-loud-fail/r36', '--output', str(output/'r36')],
        'r37': ['tools/probes/run_nested_composition.py', '--godot', str(godot), '--native',
                'evidence/importer-loud-fail/r37/native', '--output', str(output/'r37')],
        'leaf': ['tools/probes/run_bound_bitmap_component.py', '--build',
                 'evidence/importer-loud-fail/r33/native', '--godot', str(godot), '--output', str(output/'leaf')],
        'glow': ['tools/probes/run_yulong_wrapper.py', '--godot', str(godot), '--output', str(output/'glow')],
        'sampler': ['tools/probes/run_bitmap_godot_fixture.py', '--godot', str(godot), '--output', str(output/'sampler')],
        'cpu': ['tools/probes/analyze_bitmap_repeat_spans.py', '--output', str(output/'cpu.json')],
    }
    summary = {}
    for name, command in commands.items():
        process = subprocess.run(['python3', *command], cwd=ROOT, capture_output=True, text=True)
        (output/(name+'.log')).write_text(process.stdout+process.stderr)
        summary[name] = {'command': command, 'exit': process.returncode}
        print(name, process.returncode, flush=True)
    (output/'exits.json').write_text(json.dumps(summary, indent=2)+'\n')
    return all(item['exit'] == 0 for item in summary.values())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if run(args.godot.resolve(), args.output.resolve()) else 1)
