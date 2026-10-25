import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_indexed_bitmap_readback import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r148'


class IndexedBitmapReadbackTests(unittest.TestCase):
    def test_invalid_native_bitmap_is_not_treated_as_source_pixels(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['native_bitmap_properties'],['-1','-1','-1'])
        self.assertEqual(r['native_source']['status'],'invalid_bitmap')
        self.assertTrue(r['native_source']['raw_readbacks_not_interpreted'])
        self.assertEqual(r['before_after_exact'],1152)
        self.assertFalse(r['native_indexed_source_verified'])
        self.assertFalse(r['indexed_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
