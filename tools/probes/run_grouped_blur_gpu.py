"""Actual production-created buffer nodes with diagnostic integer blur and measured pass order."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
from tools.probes.analyze_blur_kernel_heldout import ROOT, decode
from tools.probes.analyze_blur_kernel_consumption import consume


def cases():
    result = []
    for case in decode(ROOT/'evidence/importer-loud-fail/r73/native'):
        i, kernel, alpha, pattern, axis, bx, by, quality, _ = case['key']
        result.append({'id': int(i), 'kernel': kernel, 'alpha': int(alpha), 'pattern': int(pattern),
                       'axis': int(axis), 'bx': bx, 'by': by, 'quality': int(quality),
                       'native': {stage: case[stage] for stage in ('input', 'filtered')}})
    return result


def compare(expected, actual):
    if len(expected) != len(actual):
        raise ValueError('GPU case coverage changed')
    scores = {stage: {'samples': len(expected)*128, 'exact': 0, 'failures': []}
              for stage in ('input', 'filtered', 'final_copy')}
    for case, row in zip(expected, actual):
        padding = [math.ceil(max(0, (k-1)/2))*case['quality'] for k in (case['bx'], case['by'])]
        axes = [axis for axis, k in enumerate((case['bx'], case['by'])) if k > 1 for _ in range(case['quality'])]
        operands = [consume((case['bx'], case['by'])[axis], 'six_significant_bits') for axis in axes]
        if (row['id'] != case['id'] or row['origin'] != [-p for p in padding] or
                row['size'] != [64+2*p for p in padding] or row['axes'] != axes or row['operands'] != operands):
            raise ValueError('GPU actual allocation/order/operands changed')
        for stage, score in scores.items():
            target = case['native']['input' if stage == 'input' else 'filtered']
            if len(row[stage]) != 128 or any(len(p) != 4 for p in row[stage]):
                raise ValueError('Incomplete GPU samples')
            for index, (p, q) in enumerate(zip(row[stage], target)):
                if p == q:
                    score['exact'] += 1
                else:
                    score['failures'].append({'case': case['id'], 'index': index, 'gpu': p, 'native': q,
                                              'kernel': case['kernel'], 'quality': case['quality'], 'axis': case['axis']})
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
        command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
                   '--quit-after', '300', '-s', 'res://tests/grouped_blur_rows.gd', '--', str(path), str(rows)]
        commands.append(command)
        process = subprocess.run(command, capture_output=True, text=True, timeout=180)
        log = process.stdout+process.stderr
        (folder/'godot.log').write_text(log)
        if process.returncode or 'ERROR' in log or f"GROUPED_BLUR_ROWS_OK cases={len(data['cases'])} production_admitted=false" not in log:
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
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    files = ['tools/probes/run_grouped_blur_gpu.py', 'tools/probes/analyze_blur_kernel_heldout.py',
             'tools/probes/analyze_blur_kernel_consumption.py', 'godot/tests/grouped_blur_rows.gd',
             'godot/tests/grouped_blur_filter_group.gd', 'godot/tests/raw_byte_texture.gdshader',
             'godot/tests/integer_blur.gdshader', 'godot/tests/consumed_extent_filter_group.gd',
             'godot/filter_group.gd', 'godot/blend_group.gd']
    provenance = {'commands': commands, 'source_sha256': {s: sha(ROOT/s) for s in files},
                  'native_sha256': {'evidence/importer-loud-fail/r73/native/native.log': sha(ROOT/'evidence/importer-loud-fail/r73/native/native.log')},
                  'readback_sha256': {'rows.json.gz': sha(output/'rows.json.gz')},
                  'godot_sha256': sha(godot), 'production_admitted': False}
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.godot.resolve(), args.output.resolve())
    print({name: (score['exact'], score['samples']) for name, score in result['scores'].items()})
    raise SystemExit(0 if result['passed'] else 1)
