#!/usr/bin/env python3
"""Strict native/GPU DropShadow regression; one changed channel fails."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/probes'))
from compare_placement_candidates import compare


def run(godot, output):
    output.mkdir(parents=True, exist_ok=True)
    fixtures = ROOT/'tools/probes/flash_filters'
    reports = []
    for name in ('drop-shadow', 'drop-shadow-extended', 'drop-shadow-ties'):
        actual = output/(name+'.json')
        fixture = fixtures/(name+'-native.json')
        command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
                   '--script', str(ROOT/'tools/probes/drop_shadow_candidate.gd'), '--', str(fixture), str(actual)]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
        (output/(name+'.log')).write_text(result.stdout)
        if result.returncode or 'ERROR' in result.stdout or not actual.exists():
            raise RuntimeError(f'{name}: renderer failed; see log')
        native = json.loads(fixture.read_text())
        report = compare(native, json.loads(actual.read_text()), 'shadow')
        (output/(name+'-comparison.json')).write_text(json.dumps(report, indent=2)+'\n')
        reports.append({'name': name, 'passed': report['passed'], 'cases': len(native)})
    (output/'summary.json').write_text(json.dumps(reports, indent=2)+'\n')
    print(json.dumps(reports))
    return all(row['passed'] for row in reports)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if run(args.godot, args.output.resolve()) else 1)
