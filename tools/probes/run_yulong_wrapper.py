#!/usr/bin/env python3
"""Compare an isolated full Yulong Glow wrapper with pinned native component images."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.probes.build_bound_bitmap_component import validate_fixture


def fixture():
    leaf = validate_fixture(json.loads((ROOT/'evidence/importer-loud-fail/r33/native/fixture.json').read_text()))
    cases = json.loads((ROOT/'evidence/importer-loud-fail/r32/components/yulong/cases.json').read_text())[:2]
    timeline = json.loads((ROOT/cases[0]['timeline']).read_text())
    validate_graph(leaf, cases, timeline)
    return {'leaf': leaf, 'cases': cases, 'production_admitted': False}


def validate_graph(leaf, cases, timeline):
    if timeline['source_swf']['sha256'] != leaf['source_sha256']:
        raise ValueError('Timeline source hash mismatch')
    if [c['id'] for c in cases] != ['yulong-157-1-1', 'yulong-159-1-1']:
        raise ValueError('Missing complete wrapper cases')
    definitions = {d['character_id']: d for d in timeline['definitions']}
    for case in cases:
        if case['samples'] != [0, 3] or case['source_frame'] != 1 or case['frame_count'] != 1 or case['source_frame_count'] != 1:
            raise ValueError('Incomplete source frame/sample coverage')
        owner = definitions[case['owner']]
        child = definitions[case['symbol']]
        if (owner['frame_count'] != 1 or child['frame_count'] != 1
                or owner['first_frame_display_list'] != [case['placement']]
                or owner['display_list_frames'] != [owner['first_frame_display_list']]
                or child['display_list_frames'] != [child['first_frame_display_list']]
                or any(owner['display_list_frame_events']) or any(child['display_list_frame_events'])):
            raise ValueError('Changed wrapper graph or unimplemented frame controls')
        placements = child['first_frame_display_list']
        if len(placements) != 1 or placements[0]['character_id'] != leaf['shape_id']:
            raise ValueError('Changed wrapper leaf graph')
        for placement in (case['placement'], placements[0]):
            if set(placement) - {'depth', 'character_id', 'matrix', 'placed_frame', 'filters'}:
                raise ValueError('Unconsumed placement field')
            m = placement['matrix']
            if any(float(m.get(k, 0)) for k in ('translateX', 'translateY', 'rotateSkew0', 'rotateSkew1')) or any(float(m.get(k, 1)) != 1 for k in ('scaleX', 'scaleY')):
                raise ValueError('Unproven effective transform')
        if placements[0].get('filters'):
            raise ValueError('Unconsumed inner filter')
        filters = case['placement'].get('filters', [])
        if len(filters) != 1 or set(filters[0]) != {'type', 'blurX', 'blurY', 'passes', 'color', 'strength'} or filters[0]['type'] != 'GLOWFILTER':
            raise ValueError('Unconsumed filter semantics')
        if case['normalization'] != {'scale': 1, 'x': 283.0, 'y': 198.5, 'bounds': [0.0, 0.0, 34.0, 3.0]}:
            raise ValueError('Unproven fractional coverage domain')
        if case['source']['sha256'] != leaf['source_sha256']:
            raise ValueError('Wrapper source mismatch')


def compare(data, output):
    identities = [(c['id'], t) for c in data['cases'] for t in c['samples']]
    if identities != [('yulong-157-1-1', 0), ('yulong-157-1-1', 3), ('yulong-159-1-1', 0), ('yulong-159-1-1', 3)]:
        raise ValueError('Incomplete or duplicate wrapper image coverage')
    if data['production_admitted'] is not False:
        raise ValueError('Diagnostic cannot admit production')
    pinned = json.loads((ROOT/'evidence/importer-loud-fail/r32/component-pixels.json').read_text())
    expected = {(r['case'], r['tick']): r['native_png_sha256'] for r in pinned['rows']}
    rows = []
    for case in data['cases']:
        for tick in case['samples']:
            name = f"{case['id']}-{tick:03d}"
            native_path = ROOT/f'evidence/importer-loud-fail/r21/components/yulong/{name}.native.png'
            digest = hashlib.sha256(native_path.read_bytes()).hexdigest()
            if digest != expected[(case['id'], tick)]:
                raise ValueError('Pinned 54-suite native image hash mismatch')
            native = Image.open(native_path).convert('RGBA')
            actual = Image.open(output/(name+'.png')).convert('RGBA')
            if native.size != (600, 400) or actual.size != native.size:
                raise ValueError('Incorrect whole-component dimensions')
            maxima, changed, mismatches = [0]*4, [0]*4, []
            for index, (a, b) in enumerate(zip(native.getdata(), actual.getdata())):
                if a == b:
                    continue
                for k in range(4):
                    maxima[k] = max(maxima[k], abs(a[k]-b[k]))
                    changed[k] += a[k] != b[k]
                mismatches.append({'x': index % 600, 'y': index // 600, 'native': a, 'diagnostic': b})
            rows.append({'case': case['id'], 'tick': tick, 'native_sha256': digest,
                         'runtime_sha256': hashlib.sha256((output/(name+'.png')).read_bytes()).hexdigest(),
                         'exact': not mismatches, 'max_channel_delta': maxima, 'changed_channels': changed,
                         'different_pixels': len(mismatches), 'mismatches': mismatches})
    report = {'images': len(rows), 'exact': sum(r['exact'] for r in rows), 'rows': rows,
              'wrapper_passed': all(r['exact'] for r in rows), 'production_admitted': False}
    (output/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def run(godot, output):
    data = fixture()
    output.mkdir(parents=True, exist_ok=True)
    path = output/'fixture.json'
    path.write_text(json.dumps(data, indent=2)+'\n')
    for case in data['cases']:
        for tick in case['samples']:
            (output/f"{case['id']}-{tick:03d}.png").unlink(missing_ok=True)
    command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
               '--quit-after', '300', '-s', 'res://tests/yulong_wrapper_diagnostic.gd', '--', str(path), str(output)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    log = result.stdout+result.stderr
    (output/'godot.log').write_text(log)
    if result.returncode or 'ERROR' in log or 'YULONG_WRAPPER_DIAGNOSTIC_RENDER_OK cases=2' not in log:
        raise ValueError('GPU did not complete cleanly')
    report = compare(data, output)
    files = ['tools/probes/run_yulong_wrapper.py', 'godot/tests/yulong_wrapper_diagnostic.gd',
             'godot/tests/wrapper_bitmap_input.gdshader', 'godot/tests/bitmap_sampler_diagnostic.gd',
             'godot/flash_filter.gdshader']
    provenance = {'command': command, 'source_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
                  'fixture_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'godot_sha256': hashlib.sha256(godot.read_bytes()).hexdigest(), 'production_admitted': False}
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.godot.resolve(), args.output.resolve())
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}))
    sys.exit(0 if report['wrapper_passed'] else 1)
