"""Compare local and concatenated scale dependence with native cache controls."""
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
    assert len(rows) == 345 and rows[-1][6:] == ['done', 'ok']
    cases = []
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
        elif kind == 'case':
            key = list(map(float, value.split(',')))
            assert len(key) == 12 and key[0] == len(cases)
            assert key[5] == key[1] and key[6] == key[2] and key[7] == key[3]
            assert key[8] == key[1]*key[2] and key[9] == key[3]
            cases.append({'key': key, 'rows': []})
        elif kind == 'flags':
            index = len(cases[-1]['rows'])
            assert value == ('0,false,false', '1,true,false', '2,false,true')[index]
        elif kind == 'pixels':
            values = [int(v) & 0xffffffff for v in value.split(',')]
            assert len(values) == 512
            cases[-1]['rows'].append(values)
        else:
            assert kind == 'done'
    assert inputs == 128 and len(cases) == 48
    lookup = {(c['key'][8],c['key'][3],c['key'][4]):c for c in cases if c['key'][1] == 1}
    results = []
    for c in cases:
        assert len(c['rows']) == 3
        baseline = lookup[(c['key'][8],c['key'][3],c['key'][4])]
        for boundary in (0,1,2):
            left,right = c['rows'][boundary],baseline['rows'][boundary]
            failed = [{'x':x,'actual_argb':a,'reference_argb':b} for x,(a,b) in enumerate(zip(left,right)) if a!=b]
            results.append({'case':int(c['key'][0]),'scale':c['key'][8],'boundary':boundary,'samples':512,'exact':512-len(failed),'failures':failed})
    return {'input_exact':inputs,'cases':cases,'comparisons':results,'candidate_admitted':False,'production_admitted':False}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.native)
    a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    for scale in (7,8):
        for boundary in (0,1,2):
            rows=[v for v in r['comparisons'] if v['scale']==scale and v['boundary']==boundary]
            print(scale,boundary,sum(v['exact'] for v in rows),sum(v['samples'] for v in rows))
