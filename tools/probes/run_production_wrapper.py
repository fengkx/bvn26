#!/usr/bin/env python3
"""Fail-closed native gate using production PNG resources, filter buffers and composition."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.probes.run_yulong_wrapper import fixture, compare

ASSET = 'godot/generated/fighters/yulong/148.png'


def validate_asset(data):
    manifest = json.loads((ROOT/'godot/generated/fighters/yulong/assets.json').read_text())
    entry = next(a for a in manifest['assets'] if a['character_id'] == data['leaf']['bitmap_id'])
    if entry['path'] != '148.png' or hashlib.sha256((ROOT/ASSET).read_bytes()).hexdigest() != entry['sha256']:
        raise ValueError('Production PNG manifest hash/path mismatch')
    return entry


def analyze_stages(data, output):
    records = json.loads((output/'buffers.json').read_text())
    if [r['case'] for r in records] != [c['id'] for c in data['cases']]:
        raise ValueError('Missing production buffer observations')
    decoded = Image.open(output/'decoded.png').convert('RGBA')
    if decoded.size != (data['leaf']['width'], data['leaf']['height']):
        raise ValueError('Unexpected decoded production texture dimensions')
    premult = [[*(c*(a+1)//256 for c in (r, g, b)), a] for r, g, b, a in decoded.getdata()]
    source = data['leaf']['pixels_premultiplied']
    texels_exact = sum(a == b for a, b in zip(premult, source))
    stages = []
    for record in records:
        if len(record['buffers']) != 1:
            raise ValueError('Unexpected production group count')
        buffer = record['buffers'][0]
        if (buffer['buffer'] != [38, 8] or buffer['global_origin'] != [281, 196]
                or buffer['source_bounds'] != [2, 2.5, 34, 3] or buffer['production_admitted'] is not False
                or buffer['texture'] != 'res://generated/fighters/yulong/148.png'
                or len(buffer['filter_passes']) != 3 or any(p['size'] != [38, 8] for p in buffer['filter_passes'])):
            raise ValueError('Unproven buffer layout or production admission claim')
        for stage in ('input', 'glow'):
            name = record['case']+'-'+stage+'.png'
            reference_path = ROOT/'evidence/importer-loud-fail/r34/wrapper'/name
            reference = Image.open(reference_path).convert('RGBA').crop((281, 196, 319, 204))
            actual = Image.open(output/name).convert('RGBA')
            if actual.size != reference.size:
                raise ValueError('Production buffer dimensions changed')
            delta = ImageChops.difference(reference, actual)
            stages.append({'case': record['case'], 'stage': stage,
                           'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
                           'runtime_sha256': hashlib.sha256((output/name).read_bytes()).hexdigest(),
                           'pixels': 304, 'exact_pixels': sum(a == b for a, b in zip(reference.getdata(), actual.getdata())),
                           'max_channel_delta': [hi for _, hi in delta.getextrema()]})
        # Independent read-only diagnosis, never substituted for actual composition.
        glow = Image.open(output/(record['case']+'-glow.png')).convert('RGBA')
        native = Image.open(ROOT/f"evidence/importer-loud-fail/r21/components/yulong/{record['case']}-000.native.png").convert('RGB')
        predicted = [tuple(v+96*(256-p[3])//256 for v in p[:3]) for p in glow.getdata()]
        stages.append({'case': record['case'], 'stage': 'integer_composition_analysis_only', 'pixels': 304,
                       'exact_pixels': sum(a == b for a, b in zip(predicted, native.crop((281,196,319,204)).getdata()))})
    return {'production_admitted': False, 'png_premultiplied_texels': len(source),
            'png_premultiplied_texels_exact': texels_exact,
            'decoded_sha256': hashlib.sha256((output/'decoded.png').read_bytes()).hexdigest(), 'stages': stages}


def path_passed(report, stages):
    measured = [s for s in stages['stages'] if s['stage'] in ('input', 'glow')]
    identities = {(s['case'], s['stage']) for s in measured}
    expected = {(case, stage) for case in ('yulong-157-1-1', 'yulong-159-1-1') for stage in ('input', 'glow')}
    return (report['wrapper_passed'] and report['images'] == report['exact'] == 4
            and report['production_admitted'] is False and stages['production_admitted'] is False
            and stages['png_premultiplied_texels'] == stages['png_premultiplied_texels_exact'] == 102
            and len(measured) == 4 and identities == expected
            and all(s['pixels'] == s['exact_pixels'] == 304 and s['max_channel_delta'] == [0, 0, 0, 0] for s in measured))


def run(godot, output):
    data = fixture()
    entry = validate_asset(data)
    output.mkdir(parents=True, exist_ok=True)
    path = output/'fixture.json'
    path.write_text(json.dumps(data, indent=2)+'\n')
    for case in data['cases']:
        for tick in case['samples']:
            (output/f"{case['id']}-{tick:03d}.png").unlink(missing_ok=True)
        for stage in ('input', 'glow'):
            (output/(case['id']+'-'+stage+'.png')).unlink(missing_ok=True)
    for name in ('buffers.json', 'decoded.png', 'comparison.json', 'stages.json'):
        (output/name).unlink(missing_ok=True)
    command = [str(godot), '--path', str(ROOT/'godot'), '--rendering-method', 'gl_compatibility',
               '--quit-after', '300', '-s', 'res://tests/production_wrapper_diagnostic.gd', '--', str(path), str(output)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    log = result.stdout+result.stderr
    (output/'godot.log').write_text(log)
    if result.returncode or 'ERROR' in log or 'PRODUCTION_WRAPPER_DIAGNOSTIC_RENDER_OK cases=2' not in log:
        raise ValueError('Production-path diagnostic did not render cleanly')
    report = compare(data, output)
    stages = analyze_stages(data, output)
    report['production_path_passed'] = path_passed(report, stages)
    (output/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    (output/'stages.json').write_text(json.dumps(stages, indent=2)+'\n')
    files = ['tools/probes/run_production_wrapper.py', 'tools/probes/run_yulong_wrapper.py',
             'godot/tests/production_wrapper_diagnostic.gd', 'godot/tests/production_sampler_preview.gd',
             'godot/tests/production_bitmap_sampler.gdshader', 'godot/tests/bitmap_sampler_diagnostic.gd',
             'godot/timeline_preview.gd', 'godot/filter_group.gd', 'godot/blend_group.gd', 'godot/flash_filter.gdshader']
    config = ROOT/(ASSET+'.import')
    if not config.is_file():
        raise ValueError('Missing production texture import configuration')
    (output/'texture-import.txt').write_bytes(config.read_bytes())
    provenance = {'command': command, 'source_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
                  'asset_manifest_entry': entry, 'texture_import_sha256': hashlib.sha256(config.read_bytes()).hexdigest(),
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
    sys.exit(0 if report['production_path_passed'] else 1)
