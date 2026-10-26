"""Compare explicit two-stage cache boundaries without using them as renderer inputs."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from tools.probes.analyze_bitmap_cache_width import ROOT


def analyze(native):
    build = json.loads((native / 'build.json').read_text())
    assert hashlib.sha256((ROOT / build['source']).read_bytes()).hexdigest() == build['source_sha256']
    path = native / 'native.log'
    text = path.read_text() if path.exists() else gzip.decompress(path.with_suffix('.log.gz').read_bytes()).decode()
    rows = [line.split('|') for line in text.splitlines() if line.startswith('AIREF|')]
    assert len(rows) == 339 and rows[-1][6:] == ['done', 'ok']
    cases = []
    inputs = 0
    for i, row in enumerate(rows):
        assert row[1] == build['run_id'] and row[2:6] == [str(i), '0', '0', '0']
        kind, value = row[6:]
        if kind == 'source':
            label, width, y, *values = value.split(',')
            assert label == 'shared' and width == '16' and int(y) == inputs // 16 and len(values) == 16
            for x, v in enumerate(values):
                assert int(v) & 0xffffffff == 0xff000000 + x % 2 * 255 * 65536 + ((x * 37 + 17) % 256) * 256 + 113
                inputs += 1
        elif kind == 'case':
            key = list(map(float, value.split(',')))
            assert len(key) == 9 and key[0] == len(cases)
            assert key[-1] == math.floor(key[6] + key[3])
            cases.append({'key': key, 'matrices': []})
        elif kind == 'cache':
            assert value in ('0,false', '1,true')
        elif kind == 'localMatrix':
            values = list(map(float, value.split(',')))
            assert values[0] == len(cases[-1]['matrices']) and len(values) == 5
            cases[-1]['matrices'].append(values)
        elif kind in ('clear', 'cached', 'local0', 'local1', 'placed0', 'placed1'):
            values = [int(v) & 0xffffffff for v in value.split(',')]
            assert len(values) == (128 if kind.startswith('local') else 512)
            assert kind not in cases[-1]
            cases[-1][kind] = values
        else:
            assert kind == 'done'
    assert len(cases) == 30 and inputs == 128
    results = []
    for c in cases:
        assert len(c['matrices']) == 2
        origin = int(c['key'][-1])
        for mode in (0, 1):
            local = c['local' + str(mode)]
            expected = [local[x-origin] if 0 <= x-origin < 128 else 0 for x in range(512)]
            for name, left, right in [('placement', c['placed'+str(mode)], expected), ('implicit_cache', c['placed'+str(mode)], c['cached']), ('uncached', c['placed'+str(mode)], c['clear'])]:
                failed = [{'x': x, 'actual_argb': a, 'reference_argb': b} for x, (a,b) in enumerate(zip(left,right)) if a != b]
                results.append({'case': int(c['key'][0]), 'mode': mode, 'comparison': name, 'samples': 512, 'exact': 512-len(failed), 'failures': failed})
    return {'input_exact': inputs, 'cases': cases, 'results': results, 'candidate_admitted': False, 'production_admitted': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.native)
    a.output.write_text(json.dumps(result,separators=(',', ':'))+'\n')
    for mode in (0,1):
        for name in ('placement','implicit_cache','uncached'):
            rows = [r for r in result['results'] if r['mode']==mode and r['comparison']==name]
            print(mode,name,sum(r['exact'] for r in rows),sum(r['samples'] for r in rows))
