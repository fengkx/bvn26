"""Validate the shared diagnostic shader against every old and signed native channel."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from PIL import Image
from tools.probes.analyze_cxform_signed_bounds import controls
from tools.probes.run_native_nested_filters import fixture, ROOT


def dataset():
    old, signed = controls()
    groups = {name: Counter((tuple(args), target) for _, args, target in rows)
              for name, rows in [('old', old), ('signed', signed)]}
    keys = sorted(set(groups['old']) | set(groups['signed']))
    return keys, groups


def compare(path, keys, groups, width=1024):
    image = Image.open(path).convert('RGBA')
    height = (len(keys) + width - 1) // width
    if image.size != (width, height):
        raise ValueError('GPU readback dimensions changed')
    pixels = list(image.getdata())
    scores = {}
    for name, counts in groups.items():
        failures = []
        for i, (args, target) in enumerate(keys):
            count = counts.get((args, target), 0)
            if not count:
                continue
            _, alpha, _, _, opacity = args
            expected = (target, target, target, alpha * (opacity * 256 // 100) // 256)
            if pixels[i] != expected:
                failures.append({'args': args, 'native': expected, 'gpu': pixels[i], 'count': count})
        total = sum(counts.values())
        scores[name] = {'channels': total, 'exact': total - sum(v['count'] for v in failures),
                        'failures': failures}
    return {'scores': scores, 'unique_controls': len(keys),
            'passed': all(not v['failures'] for v in scores.values()), 'production_admitted': False}


def run(godot, output):
    output.mkdir(parents=True, exist_ok=True)
    admission = fixture()
    keys, groups = dataset()
    width = 1024
    height = (len(keys) + width - 1) // width
    inputs, opacities = bytearray(), bytearray()
    for args, _ in keys:
        c, a, m, d, op = args
        inputs.extend(struct.pack('<4f', c, a, m, d))
        opacities.extend(struct.pack('<f', op * 256 // 100))
    inputs.extend(bytes((width * height - len(keys)) * 16))
    opacities.extend(bytes((width * height - len(keys)) * 4))
    for name, raw in [('inputs', inputs), ('opacities', opacities),
                      ('reciprocals', struct.pack('<256f', *admission['native_reciprocals']))]:
        (output / (name + '.bin')).write_bytes(raw)
    data = {'width': width, 'height': height, 'samples': len(keys), 'production_admitted': False,
            'cpu_arithmetic_passed': admission['cpu_arithmetic_passed'],
            **{name: str(output / (name + '.bin')) for name in ('inputs', 'opacities', 'reciprocals')},
            'output': str(output / 'gpu.png')}
    path = output / 'fixture.json'
    path.write_text(json.dumps(data, indent=2) + '\n')
    (output / 'gpu.png').unlink(missing_ok=True)
    command = [str(godot), '--path', str(ROOT / 'godot'), '--rendering-method', 'gl_compatibility',
               '--quit-after', '300', '-s', 'res://tests/native_cxform_controls.gd', '--', str(path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    log = result.stdout + result.stderr
    (output / 'godot.log').write_text(log)
    if result.returncode or 'ERROR' in log or f'NATIVE_CXFORM_CONTROLS_OK samples={len(keys)}' not in log:
        raise ValueError('GPU controls did not complete cleanly')
    report = compare(output / 'gpu.png', keys, groups)
    (output / 'comparison.json.gz').write_bytes(gzip.compress(json.dumps(report, indent=2).encode(), mtime=0))
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    sources = ['tools/probes/run_native_cxform_controls.py', 'godot/tests/native_cxform_controls.gd',
               'godot/tests/native_cxform_controls.gdshader', 'godot/tests/native_cxform.gdshaderinc']
    provenance = {'command': command, 'godot_sha256': sha(godot),
                  'source_sha256': {p: sha(ROOT / p) for p in sources},
                  'readback_sha256': {p: sha(output / p) for p in ('gpu.png', 'inputs.bin', 'opacities.bin', 'reciprocals.bin')},
                  'native_controls_sha256': hashlib.sha256(json.dumps(keys).encode()).hexdigest(),
                  'production_admitted': False}
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.godot.resolve(), args.output.resolve())
    print({name: (v['exact'], v['channels']) for name, v in report['scores'].items()})
    raise SystemExit(0 if report['passed'] else 1)
