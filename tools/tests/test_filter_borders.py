import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_filter_borders import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r65'


class FilterBorderTests(unittest.TestCase):
    def test_declared_extents_exact_do_not_admit_implicit_padding(self):
        report = analyze(EVIDENCE / 'native')
        for stage in ('input', 'filtered'):
            self.assertEqual(report['unchanged_stages'][stage]['exact'], 44800)
        self.assertEqual(report['declared_extent_model']['exact'], 44800)
        self.assertEqual(report['implicit_comparisons']['[0, 0]']['exact'], 6392)
        self.assertEqual(report['implicit_comparisons']['[0, 1]']['exact'], 6400)
        self.assertLess(report['implicit_comparisons']['[1, 0]']['exact'], 6400)
        self.assertFalse(report['implicit_extent_model_admitted'])
        self.assertFalse(report['production_admitted'])

    def test_source_native_and_counterexample_provenance(self):
        provenance = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', EVIDENCE / 'native'),
                          ('output_sha256', EVIDENCE)]:
            for name, digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
