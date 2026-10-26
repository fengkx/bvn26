#!/usr/bin/env python3
"""Fail-closed actual nested production buffer diagnostic, never global admission."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.probes.nested_composition import cases, inputs, predicted, decode, compare, read_atlases


def run(godot, native, output, order):
    output.mkdir(parents=True, exist_ok=True)
    references = decode(native)
    cpu = compare(references, [predicted(c) for c in cases()])
    (output/'cpu.json').write_text(json.dumps(cpu, indent=2)+'\n')
    if not cpu['passed']:
        raise ValueError('Native materialized buffer model failed')
    fixture = {'production_admitted': False, 'cases': [{'key': c, 'inputs': inputs(c)} for c in cases()]}
    path = output/'fixture.json'
    path.write_text(json.dumps(fixture)+'\n')
    for name in ('child.png', 'parent.png', 'final.png', 'buffers.json', 'comparison.json'):
        (output/name).unlink(missing_ok=True)
    command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
               '--quit-after', '300', '-s', 'res://tests/nested_buffer_diagnostic.gd', '--',
               str(path), str(output), order]
    result = subprocess.run(command, capture_output=True, text=True, timeout=240)
    log = result.stdout+result.stderr
    (output/'godot.log').write_text(log)
    if result.returncode or 'ERROR' in log or 'NESTED_BUFFER_DIAGNOSTIC_OK cases=432 order='+order not in log:
        raise ValueError('Nested buffer render did not complete cleanly')
    records = json.loads((output/'buffers.json').read_text())
    if len(records) != 432:
        raise ValueError('Missing buffer observations')
    for i, record in enumerate(records):
        if record != {'case': i, 'sizes': [[8,8],[12,8]], 'origins': [[2,0],[2,0]],
                      'production_admitted': False, 'copy_order': order}:
            raise ValueError('Unexpected actual production buffer allocation: '+str(record))
    report = compare(references, read_atlases(output))
    report['copy_order'] = order
    (output/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    files = ['tools/probes/nested_composition.py', 'tools/probes/run_nested_composition.py',
             'godot/tests/nested_buffer_preview.gd', 'godot/tests/nested_buffer_diagnostic.gd',
             'godot/tests/nested_integer_composite.gdshader', 'godot/tests/normal_composition.gdshaderinc',
             'godot/timeline_preview.gd', 'godot/blend_group.gd']
    provenance = {'command': command, 'production_admitted': False,
                  'godot_sha256': hashlib.sha256(godot.read_bytes()).hexdigest(),
                  'source_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
                  'native_sha256': {p: hashlib.sha256((native/p).read_bytes()).hexdigest() for p in ('build.json','native.log')},
                  'readback_sha256': {p: hashlib.sha256((output/p).read_bytes()).hexdigest() for p in ('child.png','parent.png','final.png','buffers.json')}}
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--copy-order', choices=('fresh', 'stale'), default='fresh')
    args = parser.parse_args()
    report = run(args.godot.resolve(), args.native.resolve(), args.output.resolve(), args.copy_order)
    print(json.dumps({'passed': report['passed'], 'production_admitted': False,
                      'scores': {s:{k:v for k,v in r.items() if k != 'failures'} for s,r in report['scores'].items()}}))
    raise SystemExit(0 if report['passed'] else 1)
