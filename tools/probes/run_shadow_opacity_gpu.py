"""Actual GPU filter and materialized blend boundaries against explicit native layers."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
from tools.probes.analyze_blur_kernel_heldout import ROOT
from tools.probes.analyze_shadow_colored_paths import decode as colored_decode
from tools.probes.analyze_shadow_materialized_opacity import decode, CONFIGS, STAGES
from tools.probes.run_colored_shadow_gpu import cases as colored_gpu_cases


def cases():
    filters = {}
    gpu = colored_gpu_cases()
    for index, case in enumerate(colored_decode(ROOT/'evidence/importer-loud-fail/r82/native')):
        _, kernel, alpha, pattern, quality, fa, strength, angle, distance, *_ = case['key']
        key = (int(case['key'][-1]), int(alpha), int(pattern), kernel, int(quality), angle, distance, fa, strength)
        if key in CONFIGS:
            for api in range(2):
                filters[CONFIGS.index(key), api] = {k: v for k, v in gpu[index*2+api].items() if k != 'native'}
    result = []
    for case in decode(ROOT/'evidence/importer-loud-fail/r84/native'):
        i, config, api, _, child, parent, *_ = case['key']
        result.append({'id': int(i), 'filter': filters[int(config), int(api)], 'child_opacity': int(child),
                       'parent_opacity': int(parent), 'back': case['back'][0], 'middle': case['middle'][0],
                       'native': {s: case[s] for s in STAGES}})
    return result


def compare(expected, actual, order):
    if len(expected) != len(actual):
        raise ValueError('Missing GPU cases')
    scores = {s: {'samples': 0, 'exact': 0, 'failures': []} for s in STAGES}
    for case, row in zip(expected, actual):
        if row['id'] != case['id'] or row['copy_order'] != order or row['sizes'] != [[64,64],[64,64]]:
            raise ValueError('Allocation/order/identity changed')
        for stage, score in scores.items():
            if len(row[stage]) != 128 or any(len(p) != 4 for p in row[stage]):
                raise ValueError('Incomplete RGBA readback')
            for index, (p, q) in enumerate(zip(row[stage], case['native'][stage])):
                score['samples'] += 1
                if p == q:
                    score['exact'] += 1
                else:
                    score['failures'].append({'case': case['id'], 'index': index, 'gpu': p, 'native': q})
    return {'scores': scores, 'copy_order': order, 'passed': all(not s['failures'] for s in scores.values()), 'production_admitted': False}


def run(godot, output, order):
    output.mkdir(parents=True, exist_ok=True)
    expected = cases()
    actual, commands = [], []
    for start in range(0, len(expected), 24):
        folder = output/str(start)
        folder.mkdir(exist_ok=True)
        data = {'production_admitted': False, 'copy_order': order, 'cases': [{k: v for k, v in c.items() if k != 'native'} for c in expected[start:start+24]]}
        path, rows = folder/'fixture.json', folder/'rows.json'
        path.write_text(json.dumps(data)+'\n')
        rows.unlink(missing_ok=True)
        command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility', '--quit-after', '300', '-s', 'res://tests/shadow_opacity_rows.gd', '--', str(path), str(rows)]
        commands.append(command)
        process = subprocess.run(command, capture_output=True, text=True, timeout=180)
        log = process.stdout+process.stderr
        (folder/'godot.log').write_text(log)
        if process.returncode or 'ERROR' in log or f"SHADOW_OPACITY_ROWS_OK cases={len(data['cases'])} order={order} production_admitted=false" not in log:
            raise ValueError('GPU batch failed: '+str(start))
        chunk = json.loads(rows.read_text())
        if [r['id'] for r in chunk] != list(range(len(data['cases']))):
            raise ValueError('Batch identities changed')
        for row in chunk:
            row['id'] += start
        actual.extend(chunk)
        print('batch', start, 'complete', flush=True)
    report = compare(expected, actual, order)
    (output/'rows.json.gz').write_bytes(gzip.compress(json.dumps(actual).encode(), mtime=0))
    (output/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    files = ['tools/probes/run_shadow_opacity_gpu.py', 'tools/probes/analyze_shadow_materialized_opacity.py', 'godot/tests/shadow_opacity_rows.gd', 'godot/tests/nested_buffer_preview.gd', 'godot/tests/nested_integer_composite.gdshader', 'godot/tests/normal_composition.gdshaderinc', 'godot/timeline_preview.gd', 'tools/probes/run_colored_shadow_gpu.py', 'tools/probes/run_integer_shadow_gpu.py', 'tools/probes/analyze_shadow_colored_paths.py', 'godot/tests/colored_shadow_rows.gd', 'godot/tests/integer_shadow.gdshader', 'godot/tests/integer_shadow_filter_group.gd', 'godot/tests/integer_shadow_rows.gd', 'godot/tests/grouped_family_filter_group.gd', 'godot/tests/grouped_blur_rows.gd', 'godot/tests/integer_blur.gdshader', 'godot/tests/raw_byte_texture.gdshader', 'godot/tests/consumed_extent_filter_group.gd', 'godot/filter_group.gd', 'godot/blend_group.gd']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    provenance = {'commands': commands, 'source_sha256': {s: sha(ROOT/s) for s in files},
                  'native_sha256': {f'evidence/importer-loud-fail/{f}/native.log': sha(ROOT/f'evidence/importer-loud-fail/{f}/native.log') for f in ('r82/native', 'r84/native')},
                  'readback_sha256': {'rows.json.gz': sha(output/'rows.json.gz')}, 'godot_sha256': sha(godot), 'production_admitted': False}
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--godot', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--copy-order', choices=('fresh', 'stale'), default='fresh')
    args = p.parse_args()
    report = run(args.godot.resolve(), args.output.resolve(), args.copy_order)
    print({k: (s['exact'], s['samples']) for k, s in report['scores'].items()})
    raise SystemExit(0 if report['passed'] else 1)
