import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_filter_extent import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r63'


class BitmapFilterExtentTests(unittest.TestCase):
    def test_materialization_retains_all_three_native_stages(self):
        report = analyze(EVIDENCE / 'native')
        self.assertTrue(report['same_native_stages'])
        self.assertEqual(sum(r['exact'] for r in report['native_equivalence'].values()), 19200)
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['pinned_gpu']['passed'])
        self.assertEqual(report['pinned_gpu']['scores']['final']['exact'], 6392)
        self.assertEqual(len(report['pinned_gpu']['scores']['final']['failures']), 8)

    def test_native_sources_and_counterexamples_preserved(self):
        provenance = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', EVIDENCE / 'native'),
                          ('output_sha256', EVIDENCE)]:
            for name, digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
