"""Strict color-order diagnostic with independently captured filter rectangle bounds."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from tools.probes.run_native_nested_filters import fixture, ROOT


def bounds(native):
    build = json.loads((native / 'build.json').read_text())
    rows = {}
    events = [line.split('|') for line in (native / 'native.log').read_text().splitlines()
              if line.startswith('AIREF|')]
    if len(events) != 65 or events[-1][6:] != ['done', 'ok']:
        raise ValueError('Incomplete native rectangle capture')
    for index, event in enumerate(events):
        if event[1] != build['run_id'] or int(event[2]) != index:
            raise ValueError('Native rectangle capture identity/order changed')
        if index == 64:
            break
        if event[6] != 'rect':
            raise ValueError('Unexpected native rectangle event')
        w, blur, kind, *rect = event[7].split(',')
        key = (int(w), int(blur), kind)
        if key in rows:
            raise ValueError('Duplicate rectangle control')
        rows[key] = list(map(int, rect))
    expected = {(w, b, kind) for w in (1, 2, 3, 15, 16, 17, 34, 64)
                for b in (1, 3, 5, 7) for kind in ('glow', 'blur')}
    if set(rows) != expected:
        raise ValueError('Native rectangle controls omitted')
    for (w, blur, _), rect in rows.items():
        pad = (blur + 1) // 2
        if rect != [40 - pad, 40 - pad, w + 2 * pad, 64 + 2 * pad]:
            raise ValueError('Measured rectangle expansion hypothesis rejected')
    return rows[(64, 5, 'glow')]


def compare(path):
    actual = json.loads(path.read_text())
    native = json.loads((ROOT / 'evidence/importer-loud-fail/r03/native-order-rows.json').read_text())
    if len(actual) != len(native) or len(actual) != 4:
        raise ValueError('Missing color-order case')
    rows = []
    for a, b in zip(actual, native):
        if (a['type'], a['opacity']) != (b['type'], b['opacity']) or len(a['pixels']) != 160:
            raise ValueError('Color-order identity/extent changed')
        if any(len(p) != 4 for p in a['pixels']):
            raise ValueError('Missing RGBA channel')
        failures = [{'x': x, 'channel': c, 'gpu': v, 'native': target}
                    for x, (p, q) in enumerate(zip(a['pixels'], b['premultiplied']))
                    for c, (v, target) in enumerate(zip(p, q)) if v != target]
        rows.append({'type': a['type'], 'opacity': a['opacity'], 'channels': 640,
                     'exact': 640 - len(failures), 'failures': failures})
    return {'rows': rows, 'groups': 4, 'exact_groups': sum(not r['failures'] for r in rows),
            'passed': all(not r['failures'] for r in rows), 'production_admitted': False}


def run(godot, native, output):
    output.mkdir(parents=True, exist_ok=True)
    data = fixture()
    data['native_glow_rect'] = bounds(native)
    path = output / 'fixture.json'
    path.write_text(json.dumps(data, indent=2) + '\n')
    rows = output / 'order.json'
    rows.unlink(missing_ok=True)
    command = [str(godot), '--path', str(ROOT / 'godot'), '--rendering-method', 'gl_compatibility',
               '--quit-after', '300', '-s', 'res://tests/native_color_order_diagnostic.gd', '--', str(rows),
               str(ROOT / 'tools/probes/flash_filters/color-matrix.json'), 'order', str(path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    log = result.stdout + result.stderr
    (output / 'godot.log').write_text(log)
    if result.returncode or 'ERROR' in log or 'NATIVE_COLOR_ORDER_BINDINGS_OK groups=4' not in log or 'FLASH_FILTERS_RENDER_OK 4' not in log:
        raise ValueError('Bounded color-order render failed')
    report = compare(rows)
    (output / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    files = ['tools/probes/run_native_color_order.py', 'tools/probes/flash_filters/filter-cache-bounds.as',
             'godot/tests/native_color_order_diagnostic.gd', 'godot/tests/native_color_order_composite.gdshader',
             'godot/tests/flash_filter_colors_render.gd', 'godot/tests/native_cxform.gdshaderinc',
             'godot/filter_group.gd', 'godot/timeline_preview.gd',
             'evidence/importer-loud-fail/r03/native-order-rows.json']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    provenance = {'command': command, 'source_sha256': {p: sha(ROOT / p) for p in files},
                  'native_sha256': {p: sha(native / p) for p in ('build.json', 'native.log')},
                  'readback_sha256': {p: sha(output / p) for p in ('fixture.json', 'order.json')},
                  'godot_sha256': sha(godot), 'production_admitted': False}
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('godot', 'native', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    report = run(args.godot.resolve(), args.native.resolve(), args.output.resolve())
    print({k: v for k, v in report.items() if k != 'rows'})
    raise SystemExit(0 if report['passed'] else 1)
