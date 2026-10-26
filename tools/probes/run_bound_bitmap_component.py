#!/usr/bin/env python3
"""Render a validated source binding and require exact native whole images."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.probes.build_bound_bitmap_component import validate_fixture
from tools.probes.compare_bound_bitmap_component import compare


def run(build, output, godot):
    fixture = validate_fixture(json.loads((build/'fixture.json').read_text()))
    output.mkdir(parents=True, exist_ok=True)
    for index in range(len(fixture['cases'])):
        (output/f'case-{index}.png').unlink(missing_ok=True)
    command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
               '--quit-after', '300', '-s', 'res://tests/bound_bitmap_component.gd', '--',
               str(build/'fixture.json'), str(output)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    log = result.stdout+result.stderr
    (output/'godot.log').write_text(log)
    if result.returncode or 'ERROR' in log or f"BOUND_BITMAP_DIAGNOSTIC_RENDER_OK cases={len(fixture['cases'])}" not in log:
        raise ValueError('GPU failed or did not complete')
    report = compare(build, output, output)
    sources = ['tools/probes/build_bound_bitmap_component.py', 'tools/probes/compare_bound_bitmap_component.py',
               'tools/probes/run_bound_bitmap_component.py', 'godot/tests/bound_bitmap_component.gd',
               'godot/tests/bitmap_sampler_diagnostic.gd', 'godot/tests/bitmap_sampler_diagnostic.gdshader']
    provenance = {'command': command, 'source_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
                  'fixture_sha256': report['fixture_sha256'], 'native_sha256': hashlib.sha256((build/'native.log').read_bytes()).hexdigest(),
                  'godot_sha256': hashlib.sha256(godot.read_bytes()).hexdigest(),
                  'readback_sha256': {f'case-{i}.png': hashlib.sha256((output/f'case-{i}.png').read_bytes()).hexdigest() for i in range(len(fixture['cases']))},
                  'production_admitted': False}
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--godot', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.build.resolve(), args.output.resolve(), args.godot.resolve())
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}))
    sys.exit(0 if report['diagnostic_passed'] else 1)
