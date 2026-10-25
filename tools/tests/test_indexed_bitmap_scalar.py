import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_indexed_bitmap_scalar import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r146'


class IndexedBitmapScalarTests(unittest.TestCase):
    def test_opaque_controls_reject_lower_weight_precision(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['source_pixels_exact'],2275)
        for api in (0,1):
            for bits,exact in ((4,335),(5,466),(6,552),(8,576)):
                self.assertEqual(r['scores'][f'api{api}-bits{bits}']['exact'],exact)
                self.assertEqual(r['scores'][f'api{api}-bits{bits}']['samples'],576)
        self.assertFalse(r['indexed_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
