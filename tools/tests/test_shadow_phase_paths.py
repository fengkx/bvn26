import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_shadow_phase_paths import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r79'


class ShadowPhasePathTests(unittest.TestCase):
    def test_api_identity_explains_heldout_phase_without_changing_display_rule(self):
        result = analyze(EVIDENCE / 'native')
        self.assertEqual(result, json.loads((EVIDENCE / 'analysis.json').read_text()))
        self.assertTrue(result['api_specific_phase_passed'])
        self.assertFalse(result['production_admitted'])
        self.assertEqual(result['common_models_passed'], [])
        self.assertEqual(result['input_exact'], 28224)
        self.assertEqual(result['scores']['even']['apply']['exact_images'], 288)
        for path in ('bitmap_display', 'vector_display'):
            self.assertEqual(result['scores']['away'][path]['exact_images'], 288)
            self.assertEqual(result['scores']['even'][path]['exact_images'], 256)
        self.assertEqual(result['old_phase']['away'], {'exact_images': 616, 'images': 616})
        self.assertEqual(result['heldout_r78_unit'], {'exact': 23040, 'samples': 23040, 'failures': [], 'native_api': 'BitmapData.applyFilter'})
        for part in result['native_equivalence'].values():
            self.assertEqual(part['parameterization_exact'], 144)
            self.assertEqual(part['origin_exact'], 144)

    def test_native_sources_and_old_phase_controls_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, base in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((base / name).read_bytes()).hexdigest(), digest)
