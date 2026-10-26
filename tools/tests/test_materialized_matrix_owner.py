import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_materialized_matrix_owner import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r197'

class MaterializedMatrixOwnerTests(unittest.TestCase):
    def test_explicit_bytes_reproduce_both_apis(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        for row in r['rows']:
            for result in row['comparisons'].values():self.assertEqual(result['exact'],result['samples'])
        self.assertEqual([sum(len(v['outputs'])>1 for v in groups) for groups in r['input_output_groups'].values()],[8,8,8])
        self.assertFalse(r['display_internal_allocation_identical_proved'])
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
