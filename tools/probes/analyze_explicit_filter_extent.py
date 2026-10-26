"""Separate explicit filter bitmap parity from unresolved implicit cache routing."""
import argparse
import hashlib
import json
from pathlib import Path
from tools.probes.analyze_bitmap_filter_extent import analyze
from tools.probes.run_native_extent_rows import ROOT


def report(native):
    result = analyze(native)
    return {'explicit_gpu': result['pinned_gpu'], 'implicit_vs_explicit': result['native_equivalence'],
            'explicit_gpu_passed': result['pinned_gpu']['passed'],
            'implicit_equivalence_passed': result['same_native_stages'],
            'passed': result['pinned_gpu']['passed'] and result['same_native_stages'],
            'production_admitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = report(args.native.resolve())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    sources = ['tools/probes/analyze_explicit_filter_extent.py', 'tools/probes/analyze_bitmap_filter_extent.py',
               'tools/probes/flash_filters/filter-explicit-extent.as', 'tools/probes/run_native_extent_rows.py',
               'evidence/importer-loud-fail/r62/native/build.json', 'evidence/importer-loud-fail/r62/native/native.log',
               'evidence/importer-loud-fail/r62/rows/rows.json']
    provenance = {'source_sha256': {p: sha(ROOT / p) for p in sources},
                  'native_sha256': {p: sha(args.native / p) for p in ('native.log', 'build.json')},
                  'output_sha256': {'analysis.json': sha(args.output / 'analysis.json')},
                  'production_admitted': False}
    (args.output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print('Explicit GPU', {k: (v['exact'], v['pixels']) for k, v in result['explicit_gpu']['scores'].items()})
    print('Implicit vs explicit', {k: (v['exact'], v['pixels']) for k, v in result['implicit_vs_explicit'].items()})
    raise SystemExit(0 if result['passed'] else 1)
