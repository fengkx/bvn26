"""Bind independently constrained API phase and gain/color bytes to diagnostic buffers."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
from tools.probes.analyze_blur_kernel_heldout import ROOT
from tools.probes.analyze_blur_kernel_consumption import consume
from tools.probes.analyze_shadow_crossed_parameters import decode as crossed_decode
from tools.probes.analyze_shadow_gain_paths import decode as ramp_decode


def cases():
    result = []
    for case in crossed_decode(ROOT/'evidence/importer-loud-fail/r78/native'):
        _, kernel, alpha, pattern, quality, _, strength, angle, distance, *_ = case['key']
        result.append({'suite': 'crossed', 'width': 64, 'height': 64, 'bx': kernel, 'by': kernel,
                       'alpha': int(alpha), 'pattern': int(pattern), 'quality': int(quality),
                       'alpha_byte': case['observed_alpha_byte'], 'strength': strength,
                       'angle': angle, 'distance': distance, 'color': [81, 211, 239], 'hidden': False, 'api': 'apply',
                       'native': {s: case[s] for s in ('input', 'blur', 'filtered')}})
    for folder, heldout in [('native', False), ('colors', True)]:
        for case in ramp_decode(ROOT/'evidence/importer-loud-fail/r80'/folder, heldout):
            _, _, strength, hidden, *_ = case['key']
            for api in ('apply', 'display'):
                result.append({'suite': folder+'_'+api, 'width': 256, 'height': 4, 'bx': 0, 'by': 0,
                               'quality': 1, 'alpha_byte': case['alpha_byte'], 'strength': strength,
                               'angle': 0, 'distance': 0, 'color': list(case['color']), 'hidden': bool(hidden), 'api': api,
                               'native': {'input': case['input' if api == 'apply' else 'display_input'], 'blur': case['input'], 'filtered': case[api]}})
    for i, case in enumerate(result):
        case['id'] = i
    return result


def compare(expected, actual):
    if len(expected) != len(actual):
        raise ValueError('Incomplete GPU coverage')
    scores = {stage: {'samples': 0, 'exact': 0, 'failures': []} for stage in ('input', 'blur', 'filtered', 'final_copy')}
    for case, row in zip(expected, actual):
        pad = [math.ceil(max(0, (k-1)/2))*case['quality']+math.ceil(abs(case['distance'])) for k in (case['bx'], case['by'])]
        axes = [axis for axis, k in enumerate((case['bx'], case['by'])) if k > 1 for _ in range(case['quality'])]
        operands = [consume((case['bx'], case['by'])[axis], 'six_significant_bits') for axis in axes]
        if (row['id'] != case['id'] or row['api'] != case['api'] or row['origin'] != [-p for p in pad] or
                row['size'] != [case['width']+2*pad[0], case['height']+2*pad[1]] or row['axes'] != axes or row['operands'] != operands):
            raise ValueError('Allocation/pass order/operand/API mismatch')
        for stage, score in scores.items():
            target = case['native']['filtered' if stage == 'final_copy' else stage]
            if len(row[stage]) != len(target) or any(len(p) != 4 for p in row[stage]):
                raise ValueError('Incomplete RGBA readback')
            for i, (p, q) in enumerate(zip(row[stage], target)):
                score['samples'] += 1
                if p == q:
                    score['exact'] += 1
                else:
                    score['failures'].append({'case': case['id'], 'suite': case['suite'], 'index': i, 'gpu': p, 'native': q})
    return {'scores': scores, 'passed': all(not s['failures'] for s in scores.values()), 'production_admitted': False}


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
        command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility', '--quit-after', '300', '-s', 'res://tests/integer_shadow_rows.gd', '--', str(path), str(rows)]
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
    files = ['tools/probes/run_integer_shadow_gpu.py', 'godot/tests/integer_shadow.gdshader', 'godot/tests/integer_shadow_filter_group.gd', 'godot/tests/integer_shadow_rows.gd', 'godot/tests/grouped_family_filter_group.gd', 'godot/tests/grouped_blur_rows.gd', 'godot/tests/integer_blur.gdshader', 'godot/tests/raw_byte_texture.gdshader', 'godot/tests/consumed_extent_filter_group.gd', 'godot/filter_group.gd', 'godot/blend_group.gd']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    provenance = {'commands': commands, 'source_sha256': {s: sha(ROOT/s) for s in files},
                  'native_sha256': {f'evidence/importer-loud-fail/{f}/native.log': sha(ROOT/f'evidence/importer-loud-fail/{f}/native.log') for f in ('r78/native', 'r80/native', 'r80/colors')},
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
