#!/usr/bin/env python3
"""Run integer-composition diagnostics against native controls and pinned wrappers."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.probes.normal_composition import PALETTES, analyze
from tools.probes.run_production_wrapper import analyze_stages, path_passed, validate_asset
from tools.probes.run_yulong_wrapper import fixture, compare


def render(godot, script, arguments, log, marker):
    command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
               '--quit-after', '300', '-s', 'res://tests/'+script, '--', *map(str, arguments)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    text = result.stdout + result.stderr
    log.write_text(text)
    if result.returncode or 'ERROR' in text or marker not in text:
        raise ValueError('Diagnostic did not render cleanly: '+str(log))
    return command


def run(godot, native, output):
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    scores = {}
    for kind in ('vector', 'bitmap'):
        result = analyze(native/kind, kind == 'vector')
        (output/(kind+'.json')).write_text(json.dumps(result, indent=2)+'\n')
        scores[kind] = {k: v for k, v in result.items() if k != 'rows'}
        for row in result['rows']:
            row['vector'] = int(kind == 'vector')
            row['colors'] = [[(c >> s) & 255 for s in (16, 8, 0)] for c in PALETTES[row['key'][1]][1:]]
            rows.append(row)
    data = {'production_admitted': False, 'rows': rows}
    path = output/'controls.json'
    path.write_text(json.dumps(data)+'\n')
    image = output/'gpu.png'
    image.unlink(missing_ok=True)
    commands = [render(godot, 'normal_composition_diagnostic.gd', [path, image], output/'gpu.log',
                       'NORMAL_COMPOSITION_DIAGNOSTIC_OK samples=4032')]
    actual = Image.open(image).convert('RGBA')
    if actual.size != (64, 63):
        raise ValueError('Unexpected GPU dimensions')
    failures = []
    for index, (pixel, row) in enumerate(zip(actual.getdata(), rows)):
        expected = row['pixels'][-1]
        if list(pixel) != expected:
            failures.append({'index': index, 'key': row['key'], 'vector': row['vector'],
                             'actual': list(pixel), 'expected': expected})
    scores['gpu'] = {'samples': len(rows), 'exact': len(rows)-len(failures), 'failures': failures}
    # A control mismatch stops before attempting the complete wrapper candidate.
    if failures or any(scores[k]['exact'] != scores[k]['samples'] for k in ('vector', 'bitmap')):
        (output/'summary.json').write_text(json.dumps(scores, indent=2)+'\n')
        raise ValueError('Native composition controls failed')
    wrapper = output/'wrapper'
    wrapper.mkdir(exist_ok=True)
    data = fixture()
    validate_asset(data)
    path = wrapper/'fixture.json'
    path.write_text(json.dumps(data, indent=2)+'\n')
    for p in wrapper.glob('*.png'):
        p.unlink()
    (wrapper/'buffers.json').unlink(missing_ok=True)
    commands.append(render(godot, 'integer_wrapper_diagnostic.gd', [path, wrapper], wrapper/'godot.log',
                           'PRODUCTION_WRAPPER_DIAGNOSTIC_RENDER_OK cases=2'))
    report = compare(data, wrapper)
    stages = analyze_stages(data, wrapper)
    (wrapper/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    (wrapper/'stages.json').write_text(json.dumps(stages, indent=2)+'\n')
    scores['wrapper'] = {k: v for k, v in report.items() if k != 'rows'}
    scores['diagnostic_passed'] = path_passed(report, stages)
    scores['production_admitted'] = False
    (output/'summary.json').write_text(json.dumps(scores, indent=2)+'\n')
    files = ['tools/probes/normal_composition.py', 'tools/probes/run_normal_composition.py',
             'godot/tests/normal_composition.gdshaderinc', 'godot/tests/normal_composition.gdshader',
             'godot/tests/normal_composition_diagnostic.gd', 'godot/tests/integer_wrapper_diagnostic.gd',
             'godot/tests/production_wrapper_diagnostic.gd', 'godot/tests/production_sampler_preview.gd',
             'godot/timeline_preview.gd', 'godot/filter_group.gd', 'godot/blend_group.gd']
    provenance = {'commands': commands, 'production_admitted': False,
                  'godot_sha256': hashlib.sha256(godot.read_bytes()).hexdigest(),
                  'source_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
                  'native_sha256': {kind+'/'+name: hashlib.sha256((native/kind/name).read_bytes()).hexdigest()
                                    for kind in ('vector', 'bitmap') for name in ('build.json', 'native.log')},
                  'gpu_sha256': hashlib.sha256(image.read_bytes()).hexdigest()}
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    return scores


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.godot.resolve(), args.native.resolve(), args.output.resolve())
    print(json.dumps(result))
    raise SystemExit(0 if result['diagnostic_passed'] else 1)
