import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_matrix_span_origins import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r199'

class MatrixSpanOriginsTests(unittest.TestCase):
    def test_span_origins_and_opaque_neighbor_color_are_independent(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['cases'],1728)
        self.assertEqual(r['origin_invariant_groups'],192)
        self.assertEqual(r['neighbor_color_invariant_groups'],432)
        self.assertFalse(r['arithmetic_admitted'])
        self.assertFalse(r['partition_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
