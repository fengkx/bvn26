import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_matrix_neighbor_alpha import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r198'

class MatrixNeighborAlphaTests(unittest.TestCase):
    def test_fixed_target_depends_on_neighbor_alpha(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['target_source_exact'],2048)
        self.assertEqual(r['changed_target_groups'],92)
        self.assertTrue(all(not v['changed_by_neighbor_mask'] for v in r['groups'] if v['neighbor_alpha']==127))
        self.assertFalse(r['arithmetic_admitted'])
        self.assertFalse(r['partition_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
