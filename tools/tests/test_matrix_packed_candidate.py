import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_matrix_packed_candidate import analyze
from tools.probes.matrix_packed_candidate import coefficients, render
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r204'

class MatrixPackedCandidateTests(unittest.TestCase):
    def test_all_independent_rgba_controls_and_materialized_boundaries(self):
        result=analyze()
        self.assertEqual(result,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(sum(r['samples'] for r in result['comparisons'].values()),554400)
        self.assertTrue(result['measured_rgba_exact'])
        self.assertFalse(result['gpu_advance_allowed'])
        self.assertFalse(result['production_admitted'])

    def test_unproven_alpha_and_range_fail_closed(self):
        matrix=[1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,1,0]
        changed=matrix[:];changed[19]=1
        with self.assertRaises(ValueError):coefficients(changed)
        changed=matrix[:];changed[0]=100
        with self.assertRaises(ValueError):coefficients(changed)
        with self.assertRaises(ValueError):render([[128,0,0,64]],1,matrix)

    def test_provenance(self):
        proof=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in proof[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
