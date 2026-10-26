import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_indexed_alpha_scalar import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r147'


class IndexedAlphaScalarTests(unittest.TestCase):
    def test_unverified_indexed_input_cannot_admit_weight_math(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['source_pixels_exact'],2275)
        self.assertEqual(r['scores']['api1-bits8']['exact'],576)
        self.assertTrue(r['all_indexed_samples_transparent'])
        self.assertFalse(r['native_indexed_texels_read_back'])
        self.assertFalse(r['indexed_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
