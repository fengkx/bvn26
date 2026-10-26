"""Compare cache boundary ownership at explicit effective-transform controls."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_bitmap_cache_width import ROOT


def analyze(native):
    build = json.loads((native / 'build.json').read_text())
    assert hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest() == build['source_sha256']
    p = native / 'native.log'
    text = p.read_text() if p.exists() else gzip.decompress(p.with_suffix('.log.gz').read_bytes()).decode()
    rows = [s.split('|') for s in text.splitlines() if s.startswith('AIREF|')]
    assert len(rows) == 459 and rows[-1][6:] == ['done', 'ok']
    groups = []
    inputs = 0
    for i, r in enumerate(rows):
        assert r[1] == build['run_id'] and r[2:6] == [str(i), '0', '0', '0']
        kind, value = r[6:]
        if kind == 'source':
            label, width, y, *values = value.split(',')
            assert label == 'shared' and width == '16' and int(y) == inputs // 16 and len(values) == 16
            for x, v in enumerate(values):
                assert int(v) & 0xffffffff == 0xff000000 + x % 2 * 255 * 65536 + ((x * 37 + 17) % 256) * 256 + 113
                inputs += 1
        elif kind == 'group':
            key = list(map(float, value.split(',')))
            assert len(key) == 4 and key[0] == len(groups)
            groups.append({'key': key, 'routes': []})
        elif kind == 'route':
            key = list(map(float, value.split(',')))
            assert len(key) == 10 and key[0] == len(groups[-1]['routes'])
            groups[-1]['routes'].append({'key': key, 'rows': []})
        elif kind == 'flags':
            index = len(groups[-1]['routes'][-1]['rows'])
            assert value == ('0,false,false', '1,true,false', '2,false,true')[index]
        elif kind == 'pixels':
            values = [int(v) & 0xffffffff for v in value.split(',')]
            assert len(values) == 512
            groups[-1]['routes'][-1]['rows'].append(values)
        else:
            assert kind == 'done'
    assert inputs == 128 and len(groups) == 30
    comparisons = []
    for g in groups:
        assert len(g['routes']) == 2 and all(len(r['rows']) == 3 for r in g['routes'])
        assert g['routes'][0]['key'][6:8] == g['routes'][1]['key'][6:8]
        for route in (0, 1):
            rows = g['routes'][route]['rows']
            for name, left, right in [('child_parent', rows[1], rows[2]), ('clear_child', rows[0], rows[1]), ('clear_parent', rows[0], rows[2])]:
                failed = [{'x': x, 'left_argb': a, 'right_argb': b} for x, (a,b) in enumerate(zip(left,right)) if a != b]
                comparisons.append({'group': int(g['key'][0]), 'route': route, 'comparison': name, 'samples': 512, 'exact': 512-len(failed), 'failures': failed})
        for boundary in (0, 1, 2):
            failed = [{'x': x, 'left_argb': a, 'right_argb': b} for x, (a,b) in enumerate(zip(g['routes'][0]['rows'][boundary],g['routes'][1]['rows'][boundary])) if a != b]
            comparisons.append({'group': int(g['key'][0]), 'route': 'moved', 'comparison': str(boundary), 'samples': 512, 'exact': 512-len(failed), 'failures': failed})
    from tools.probes.analyze_bitmap_cache_materialized import analyze as materialized
    prior = materialized(ROOT / 'evidence/importer-loud-fail/r105/native')
    explicit_parent = []
    for c, g in zip(prior['cases'], groups):
        assert c['key'][:4] == g['key']
        left, right = c['placed0'], g['routes'][0]['rows'][2]
        failed = [{'x': x, 'explicit_argb': a, 'parent_cache_argb': b} for x, (a,b) in enumerate(zip(left,right)) if a != b]
        explicit_parent.append({'group': int(g['key'][0]), 'samples': 512, 'exact': 512-len(failed), 'failures': failed})
    return {'explicit_parent': explicit_parent, 'input_exact': inputs, 'groups': groups, 'comparisons': comparisons, 'candidate_admitted': False, 'production_admitted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    r = analyze(a.native)
    a.output.write_text(json.dumps(r,separators=(',', ':'))+'\n')
    for route, name in dict.fromkeys((v['route'],v['comparison']) for v in r['comparisons']):
        rows = [v for v in r['comparisons'] if (v['route'],v['comparison']) == (route,name)]
        print(route,name,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows))
