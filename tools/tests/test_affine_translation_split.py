import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_translation_split import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r165'

class AffineTranslationSplitTests(unittest.TestCase):
    def test_integer_translation_routes_retain_native_indices(self):
        r=analyze(EVIDENCE/'native',ROOT/'evidence/importer-loud-fail/r164/summary.json')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['invariant_groups'],40)
        self.assertEqual(r['samples'],360)
        self.assertEqual(r['old_baseline'],{'samples':40,'exact':40})
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
