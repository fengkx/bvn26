import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_glow_shadow_multipass import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r76'


class GlowShadowMultipassTests(unittest.TestCase):
    def test_independent_families_reject_alternating_and_reverse_order(self):
        result = analyze(EVIDENCE / 'native')
        self.assertEqual(result, json.loads((EVIDENCE / 'analysis.json').read_text()))
        self.assertTrue(result['bounded_cpu_passed'])
        self.assertFalse(result['production_admitted'])
        self.assertEqual(result['input_exact'], 69120)
        self.assertEqual(result['independent_blur'], {'exact': 69120, 'samples': 69120, 'failures': []})
        for orders in result['families'].values():
            self.assertEqual({name: score['exact'] for name, score in orders.items()},
                             {'grouped': 34560, 'alternating': 34221, 'grouped_vertical_first': 33873})
            self.assertFalse(orders['grouped']['failures'])
            for failure in orders['alternating']['failures']:
                self.assertEqual(failure['axis'], 2)
                self.assertIn(failure['quality'], (2, 3))

    def test_native_and_sources_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, base in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((base / name).read_bytes()).hexdigest(), digest)
