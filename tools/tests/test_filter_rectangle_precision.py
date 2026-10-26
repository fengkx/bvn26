import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_filter_rectangle_precision import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r67'


class FilterRectanglePrecisionTests(unittest.TestCase):
    def test_public_controls_reject_float32_input_without_admitting_cache(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r['property_text_matches'], 420)
        self.assertTrue(r['public_rectangle_controls_passed'])
        for kind in ('glow', 'blur'):
            self.assertEqual(r['scores'][kind]['double_input']['exact'], 210)
            self.assertEqual(r['scores'][kind]['float32_input']['exact'], 187)
        self.assertFalse(r['implicit_extent_model_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_native_properties_and_sources_remain_pinned(self):
        provenance = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', EVIDENCE / 'native'),
                          ('output_sha256', EVIDENCE)]:
            for name, digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
