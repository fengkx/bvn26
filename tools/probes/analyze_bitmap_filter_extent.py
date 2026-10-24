"""Compare independently materialized bitmap input to pinned vector filter stages."""
import argparse
import hashlib
import json
from pathlib import Path

from tools.probes.run_native_extent_rows import decode, compare, ROOT


def analyze(bitmap):
    vector_path = ROOT / 'evidence/importer-loud-fail/r62/native'
    vector, materialized = decode(vector_path), decode(bitmap)
    scores = {}
    for stage in ('input', 'filtered', 'final'):
        failures = []
        for a, b in zip(vector, materialized):
            for field in ('id', 'width', 'left', 'opacity', 'rect'):
                if a[field] != b[field]:
                    raise ValueError('Bitmap/vector geometry differs')
            for x, (p, q) in enumerate(zip(a[stage], b[stage])):
                if p != q:
                    failures.append({'id': a['id'], 'x': x, 'vector': p, 'bitmap': q})
        scores[stage] = {'pixels': 6400, 'exact': 6400 - len(failures), 'failures': failures}
    gpu_path = ROOT / 'evidence/importer-loud-fail/r62/rows/rows.json'
    gpu = compare(materialized, json.loads(gpu_path.read_text()))
    return {'native_equivalence': scores, 'same_native_stages': all(not r['failures'] for r in scores.values()),
            'pinned_gpu': gpu, 'production_admitted': False,
            'scope': 'Same native input/filter/final rows do not explain implicit cache allocation or routing.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.native.resolve())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    files = ['tools/probes/analyze_bitmap_filter_extent.py', 'tools/probes/flash_filters/filter-bitmap-extent.as',
             'tools/probes/run_native_extent_rows.py', 'evidence/importer-loud-fail/r62/native/build.json',
             'evidence/importer-loud-fail/r62/native/native.log', 'evidence/importer-loud-fail/r62/rows/rows.json']
    provenance = {'source_sha256': {p: sha(ROOT / p) for p in files},
                  'native_sha256': {p: sha(args.native / p) for p in ('native.log', 'build.json')},
                  'output_sha256': {'analysis.json': sha(args.output / 'analysis.json')},
                  'production_admitted': False}
    (args.output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print('Native equivalence', {k: (v['exact'], v['pixels']) for k, v in report['native_equivalence'].items()})
    print('Pinned GPU', {k: (v['exact'], v['pixels']) for k, v in report['pinned_gpu']['scores'].items()})
    raise SystemExit(0 if report['pinned_gpu']['passed'] else 1)
