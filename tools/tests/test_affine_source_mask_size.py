import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_source_mask_size import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r164'

class AffineSourceMaskSizeTests(unittest.TestCase):
    def test_independent_sizes_preserve_common_interior_indices(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['source_texels_exact'],16640)
        self.assertEqual(r['invariant_groups'],160)
        self.assertEqual(r['samples'],640)
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
