"""Run pinned non-white input bytes through the unchanged r81 diagnostic shader."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
from tools.probes.analyze_blur_kernel_heldout import ROOT
from tools.probes.analyze_blur_kernel_consumption import consume
from tools.probes.analyze_shadow_colored_paths import decode as colored_decode
from tools.probes.run_integer_shadow_gpu import compare


def cases():
    result = []
    for case in colored_decode(ROOT/'evidence/importer-loud-fail/r82/native'):
        _, kernel, alpha, pattern, quality, _, strength, angle, distance, *_ = case['key']
        row = case['input'][:64]
        assert case['input'][64:] == [row[32] if 24 <= y <= 40 else [0]*4 for y in range(64)]
        for api, output in [('apply', 'filtered'), ('display', 'display')]:
            result.append({'id': len(result), 'suite': 'colored_'+api, 'width': 64, 'height': 64,
                           'bx': kernel, 'by': kernel, 'quality': int(quality),
                           'alpha_byte': case['alpha_byte'], 'strength': strength,
                           'angle': angle, 'distance': distance, 'color': [81, 211, 239], 'hidden': False, 'api': api,
                           'source_row': row,
                           'native': {'input': case['input'], 'blur': case['blur'], 'filtered': case[output]}})
    return result


def run(godot, output):
    output.mkdir(parents=True, exist_ok=True)
    expected = cases()
    actual, commands = [], []
    for start in range(0, len(expected), 48):
        folder = output/str(start)
        folder.mkdir(exist_ok=True)
        data = {'production_admitted': False, 'cases': [{k: v for k, v in c.items() if k != 'native'} for c in expected[start:start+48]]}
        path, rows = folder/'fixture.json', folder/'rows.json'
        path.write_text(json.dumps(data)+'\n')
        rows.unlink(missing_ok=True)
        command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility', '--quit-after', '300', '-s', 'res://tests/colored_shadow_rows.gd', '--', str(path), str(rows)]
        commands.append(command)
        process = subprocess.run(command, capture_output=True, text=True, timeout=180)
        log = process.stdout+process.stderr
        (folder/'godot.log').write_text(log)
        if process.returncode or 'ERROR' in log or f"INTEGER_SHADOW_ROWS_OK cases={len(data['cases'])} production_admitted=false" not in log:
            raise ValueError('GPU batch failed: '+str(start))
        chunk = json.loads(rows.read_text())
        if [r['id'] for r in chunk] != list(range(len(data['cases']))):
            raise ValueError('Batch identities changed')
        for row in chunk:
            row['id'] += start
        actual.extend(chunk)
        print('batch', start, 'complete', flush=True)
    report = compare(expected, actual)
    (output/'rows.json.gz').write_bytes(gzip.compress(json.dumps(actual).encode(), mtime=0))
    (output/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    files = ['tools/probes/run_colored_shadow_gpu.py', 'tools/probes/run_integer_shadow_gpu.py', 'tools/probes/analyze_shadow_colored_paths.py', 'godot/tests/colored_shadow_rows.gd', 'godot/tests/integer_shadow.gdshader', 'godot/tests/integer_shadow_filter_group.gd', 'godot/tests/integer_shadow_rows.gd', 'godot/tests/grouped_family_filter_group.gd', 'godot/tests/grouped_blur_rows.gd', 'godot/tests/integer_blur.gdshader', 'godot/tests/raw_byte_texture.gdshader', 'godot/tests/consumed_extent_filter_group.gd', 'godot/filter_group.gd', 'godot/blend_group.gd']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    provenance = {'commands': commands, 'source_sha256': {s: sha(ROOT/s) for s in files},
                  'native_sha256': {f'evidence/importer-loud-fail/{f}/native.log': sha(ROOT/f'evidence/importer-loud-fail/{f}/native.log') for f in ('r82/native',)},
                  'readback_sha256': {'rows.json.gz': sha(output/'rows.json.gz')}, 'godot_sha256': sha(godot), 'production_admitted': False}
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--godot', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    report = run(args.godot.resolve(), args.output.resolve())
    print({k: (s['exact'], s['samples']) for k, s in report['scores'].items()})
    raise SystemExit(0 if report['passed'] else 1)
