#!/usr/bin/env python3
"""Run the native-backed Godot diagnostic; reject missing or inexact GPU evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.probes.build_bitmap_godot_fixture import build

ROOT = Path(__file__).resolve().parents[2]


def validate_report(report, fixture, fixture_hash):
    if (report.get('fixture_sha256') != fixture_hash or report.get('production_admitted') is not False
            or report.get('samples') != fixture['samples'] or report.get('exact') != fixture['samples']
            or report.get('failures') != []):
        raise ValueError('Incomplete or inexact native GPU comparison')
    expected = {}
    for case in fixture['cases']:
        expected[case['suite']] = expected.get(case['suite'], 0) + len(case.get('row_expected', [0]))
    if report.get('scores') != {key: {'samples': count, 'exact': count} for key, count in expected.items()}:
        raise ValueError('GPU suite coverage mismatch')


def run(godot, output):
    output.mkdir(parents=True, exist_ok=True)
    fixture = build()
    path = output/'fixture.json'
    path.write_text(json.dumps(fixture, separators=(',', ':'))+'\n')
    report_path = output/'gpu.json'
    report_path.unlink(missing_ok=True)
    command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
               '--quit-after', '600', '-s', 'res://tests/bitmap_sampler_native_render.gd', '--',
               str(path), str(report_path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    log = result.stdout+result.stderr
    (output/'gpu.log').write_text(log)
    marker = f"BITMAP_NATIVE_GPU_REFERENCE_OK samples={fixture['samples']} exact={fixture['samples']}"
    if result.returncode or 'ERROR' in log or marker not in log or not report_path.exists():
        raise ValueError('GPU diagnostic failed, timed out, or did not complete; see gpu.log')
    report = json.loads(report_path.read_text())
    validate_report(report, fixture, hashlib.sha256(path.read_bytes()).hexdigest())
    files = ['godot/tests/bitmap_sampler_diagnostic.gd',
             'godot/tests/bitmap_sampler_diagnostic.gdshader',
             'godot/tests/bitmap_sampler_native_render.gd',
             'tools/probes/build_bitmap_godot_fixture.py', 'tools/probes/run_bitmap_godot_fixture.py']
    evidence = {'command': command, 'fixture_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'reference_sha256': fixture['reference_sha256'],
                'source_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
                'godot_sha256': hashlib.sha256(godot.read_bytes()).hexdigest(),
                'readback_sha256': hashlib.sha256((output/'gpu.png').read_bytes()).hexdigest(),
                'production_admitted': False}
    (output/'provenance.json').write_text(json.dumps(evidence, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.godot.resolve(), args.output.resolve())
    print(json.dumps({key: report[key] for key in ('samples', 'exact', 'scores', 'production_admitted')}))
