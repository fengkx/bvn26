import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_conservative_filter_extent import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r68'


class ConservativeFilterExtentTests(unittest.TestCase):
    def test_integer_success_cannot_admit_fractional_failures(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r['prior_integer_controls']['exact'], 46720)
        self.assertEqual(r['new_explicit_model']['exact'], 38400)
        self.assertEqual(r['new_native_comparisons']['filtered']['exact'], 38400)
        final = r['new_native_comparisons']['final']
        self.assertEqual(final['exact'], 38218)
        self.assertEqual({v['key'][4] for v in final['failures']}, {3.5, 3.99609375, 7.5, 7.99609375})
        self.assertFalse(r['conservative_model_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_sources_and_counterexamples_remain_pinned(self):
        provenance = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', EVIDENCE / 'native'),
                          ('output_sha256', EVIDENCE)]:
            for name, digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
