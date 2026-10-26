import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_transform_paths import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r161'

class AffineTransformPathTests(unittest.TestCase):
    def test_paths_match_without_admitting_initializer(self):
        r=analyze(EVIDENCE/'native',ROOT/'evidence/importer-loud-fail/r158/native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['old_child_path'],{'samples':256000,'exact':256000})
        self.assertEqual(r['path_comparison']['exact'],256000)
        self.assertEqual(r['path_comparison']['interior_exact'],22261)
        self.assertTrue(r['fill_matrix_is_declared_not_internal_readback'])
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
