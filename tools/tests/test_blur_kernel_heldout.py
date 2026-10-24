import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_blur_kernel_heldout import analyze, render

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r73'


class BlurKernelHeldoutTests(unittest.TestCase):
    def test_grouped_axes_retain_old_and_heldout_native_controls(self):
        result = analyze(EVIDENCE / 'native')
        self.assertEqual(result, json.loads((EVIDENCE / 'analysis.json').read_text()))
        self.assertTrue(result['bounded_cpu_passed'])
        self.assertFalse(result['current_production_order_passed'])
        self.assertFalse(result['production_admitted'])
        self.assertEqual(result['input_exact'], 165888)
        self.assertEqual(result['regressions'], {'r71': {'exact': 10080, 'samples': 10080},
                                                'r72': {'exact': 72576, 'samples': 72576}})
        self.assertEqual({name: score['exact'] for name, score in result['orders'].items()},
                         {'alternating': 164159, 'grouped': 165888, 'grouped_vertical_first': 162446})
        self.assertFalse(result['orders']['grouped']['failures'])
        for failure in result['orders']['alternating']['failures']:
            self.assertEqual(failure['axis'], 2)
            self.assertIn(failure['quality'], (2, 3))

    def test_unknown_order_rejects(self):
        with self.assertRaises(ValueError):
            render([[0]], 1, 1, 1, 'unknown')

    def test_native_and_sources_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, base in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((base / name).read_bytes()).hexdigest(), digest)
