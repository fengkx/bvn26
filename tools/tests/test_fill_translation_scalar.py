import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_fill_translation_scalar import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r143'


class FillTranslationScalarTests(unittest.TestCase):
    def test_coincident_candidates_do_not_imply_admission(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(len(r['source_pixels']),64)
        for v in r['scores'].values():
            self.assertEqual(v['exact'],1152)
            self.assertEqual(v['samples'],1152)
        self.assertFalse(r['fill_translation_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
