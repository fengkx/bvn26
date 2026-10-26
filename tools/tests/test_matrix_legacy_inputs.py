import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_matrix_legacy_inputs import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r206'

class MatrixLegacyInputsTests(unittest.TestCase):
    def test_original_outputs_and_fixed_arithmetic(self):
        result=analyze(EVIDENCE/'scalar',EVIDENCE/'ramp')
        self.assertEqual(result,json.loads(gzip.decompress((EVIDENCE/'summary.json.gz').read_bytes())))
        self.assertTrue(result['original_outputs_unchanged'])
        self.assertEqual(result['comparisons']['scalar']['exact'],24)
        self.assertEqual(result['comparisons']['ramp']['exact'],2048)
        self.assertFalse(result['production_admitted'])

    def test_provenance(self):
        proof=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in proof[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
