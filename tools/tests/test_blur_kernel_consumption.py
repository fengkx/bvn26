import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_blur_kernel_consumption import analyze, consume

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r72'


class BlurKernelConsumptionTests(unittest.TestCase):
    def test_common_construction_retains_old_and_fresh_native_controls(self):
        result = analyze(EVIDENCE / 'native')
        self.assertEqual(result, json.loads((EVIDENCE / 'analysis.json').read_text()))
        self.assertTrue(result['bounded_cpu_passed'])
        self.assertFalse(result['production_admitted'])
        for name, count in [('old', 10080), ('fresh', 72576)]:
            self.assertEqual(result[name]['input_exact'], count)
            score = result[name]['models']['six_significant_bits']
            self.assertEqual((score['exact'], score['samples'], score['failures']), (count, count, []))
            self.assertTrue(result[name]['models']['fixed_four_fraction_bits']['failures'])
        self.assertEqual(result['prior_blur_operands_unchanged'], {'exact': 242, 'cases': 242})

    def test_invalid_operands_and_unknown_constructions_reject(self):
        for value in (-1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                consume(value, 'six_significant_bits')
        with self.assertRaises(ValueError):
            consume(3.5, 'unknown')

    def test_native_and_sources_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, base in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((base / name).read_bytes()).hexdigest(), digest)
