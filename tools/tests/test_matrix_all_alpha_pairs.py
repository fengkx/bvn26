import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_matrix_all_alpha_pairs import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r205'

class MatrixAllAlphaPairsTests(unittest.TestCase):
    def test_explicit_inputs_and_rejected_common_arithmetic(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'summary.json.gz').read_bytes())))
        self.assertEqual(r['comparison']['samples'],55296)
        self.assertEqual(r['comparison']['exact'],55296)
        self.assertFalse(r['gpu_advance_allowed'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
