import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_shadow_materialized_opacity import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r84'


class ShadowMaterializedOpacityTests(unittest.TestCase):
    def test_explicit_boundaries_are_exact_and_cannot_be_collapsed(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r, json.loads((EVIDENCE / 'analysis.json').read_text()))
        self.assertTrue(r['passed'])
        self.assertFalse(r['production_admitted'])
        for score in r['scores'].values():
            self.assertEqual(score, {'samples': 46080, 'exact': 46080, 'failures': []})
        self.assertEqual(r['collapsed_final_exact'], 38254)
        self.assertEqual(r['collapsed_final_samples'], 46080)

    def test_native_inputs_and_old_composition_model_are_pinned(self):
        data = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in data[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
