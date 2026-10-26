import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_png_decode import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r86'


class PngDecodeTests(unittest.TestCase):
    def test_external_png_path_rejects_constructor_and_leaf_generalization(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r, json.loads(gzip.decompress((EVIDENCE / 'analysis.json.gz').read_bytes())))
        self.assertEqual(r['passed_models'], ['opaque_or_floor_256'])
        self.assertEqual(r['source_rgba_exact'], 196608)
        self.assertEqual(r['native_alpha_exact'], 196608)
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])
        self.assertEqual(r['scores']['opaque_or_floor_256']['exact'], 196608)
        self.assertEqual(r['scores']['alpha_plus_one_256']['exact'], 21839)
        self.assertEqual(r['scores']['nearest_255']['exact'], 9806)
        self.assertEqual(r['scores']['floor_255']['exact'], 68472)

    def test_encoded_png_and_native_capture_are_pinned(self):
        data = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in data[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
