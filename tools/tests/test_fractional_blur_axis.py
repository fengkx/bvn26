import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_fractional_blur_axis import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r71'


class FractionalBlurAxisTests(unittest.TestCase):
    def test_explicit_native_bytes_reject_all_common_candidates(self):
        result = analyze(EVIDENCE / 'native')
        self.assertEqual(result, json.loads((EVIDENCE / 'analysis.json').read_text()))
        self.assertEqual(result['input_exact'], 10080)
        self.assertFalse(result['production_admitted'])
        self.assertEqual({k: v['exact'] for k, v in result['models'].items()}, {
            'rational': 9884, 'weight8': 8767, 'reciprocal16': 7947,
            'weight8_reciprocal16': 7936, 'weight8_renormalized': 9894})
        for score in result['models'].values():
            self.assertTrue(score['failures'])

    def test_native_and_sources_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, base in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((base / name).read_bytes()).hexdigest(), digest)
