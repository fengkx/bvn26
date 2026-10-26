import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_shadow_gain_paths import analyze, shadow_bytes

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r80'


class ShadowGainPathTests(unittest.TestCase):
    def test_common_byte_construction_clears_independent_colors_and_crossed_controls(self):
        result = analyze(EVIDENCE / 'native', EVIDENCE / 'colors')
        self.assertEqual(result, json.loads(gzip.decompress((EVIDENCE / 'analysis.json.gz').read_bytes())))
        self.assertTrue(result['candidate_passed'])
        self.assertFalse(result['production_admitted'])
        for name, samples in [('ramps', 4608), ('heldout_colors', 12288)]:
            part = result[name]
            self.assertEqual(part['input_exact'], samples*2)
            self.assertEqual(part['native_api_pair_exact'], samples)
            for path in ('apply', 'display'):
                self.assertEqual(part['scores']['premultiplied_color'][path], {'exact': samples, 'samples': samples, 'failures': []})
                for model in ('continuous_gain', 'byte_gain_floor', 'byte_gain_nearest'):
                    self.assertTrue(part['scores'][model][path]['failures'])
        self.assertEqual(result['heldout_r78']['exact'], 207360)
        self.assertEqual(result['heldout_r78']['failures'], [])

    def test_native_sources_and_readbacks_are_pinned(self):
        data = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, base in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for path, digest in data[key].items():
                self.assertEqual(hashlib.sha256((base / path).read_bytes()).hexdigest(), digest)
        with self.assertRaises(ValueError):
            shadow_bytes(25, 127, 1, 'unknown')
