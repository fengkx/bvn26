import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_png_draw_paths import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r87'


class PngDrawPathTests(unittest.TestCase):
    def test_independent_mixed_alpha_draw_paths_preserve_candidate_bytes(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r, json.loads((EVIDENCE / 'analysis.json').read_text()))
        self.assertTrue(r['bounded_external_png_passed'])
        self.assertFalse(r['internal_decoder_attribution_proven'])
        self.assertFalse(r['production_admitted'])
        self.assertEqual(r['source_rgba_exact'], 4096)
        for score in r['scores'].values():
            self.assertEqual(score, {'samples':4096, 'exact':4096, 'failures':[]})
        self.assertEqual(r['native_equivalence'], {'direct_black':4096, 'single_clip':4096, 'redraw':4096})

    def test_encoded_inputs_and_native_sources_are_pinned(self):
        data = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in data[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
