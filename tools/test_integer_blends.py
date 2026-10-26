#!/usr/bin/env python3
"""Strict native/GPU placement blend regression; one changed channel fails."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/probes'))
from compare_placement_candidates import compare
from analyze_placement_arithmetic import grid_report


def run(godot, output):
    output.mkdir(parents=True, exist_ok=True)
    fixtures = ROOT/'tools/probes/flash_filters'
    reports = []
    for name in ('placement-blend', 'blend-alpha-ramp', 'blend-alpha-boundaries', 'blend-layered', 'placement-overlay-grid'):
        actual = output/(name+'.json')
        grid = name == 'placement-overlay-grid'
        script = 'placement_overlay_grid_candidate.gd' if grid else 'placement_blend_candidate.gd'
        args = [str(actual)] if grid else [str(fixtures/(name+'-native.json')), str(actual)]
        command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
                   '--script', str(ROOT/'tools/probes'/script), '--', *args]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
        (output/(name+'.log')).write_text(result.stdout)
        if result.returncode or 'ERROR' in result.stdout or not actual.exists():
            raise RuntimeError(f'{name}: renderer failed; see log')
        native = json.loads((fixtures/(name+'-native.json')).read_text())
        observed = json.loads(actual.read_text())
        report = grid_report(native, observed) if grid else compare(native, observed, 'blend')
        passed = not report['gpu_differences'] and not report['model_differences'] if grid else report['passed']
        (output/(name+'-comparison.json')).write_text(json.dumps(report, indent=2)+'\n')
        reports.append({'name': name, 'passed': passed, 'cases': 65536 if grid else len(native)})
    (output/'summary.json').write_text(json.dumps(reports, indent=2)+'\n')
    print(json.dumps(reports))
    return all(row['passed'] for row in reports)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if run(args.godot, args.output.resolve()) else 1)
