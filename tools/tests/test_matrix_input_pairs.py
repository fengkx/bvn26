import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_matrix_input_pairs import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r196'

class MatrixInputPairsTests(unittest.TestCase):
    def test_separate_cache_snapshots_do_not_prove_pointwise_input(self):
        r=analyze()
        locations={str(i):v.pop('locations') for i,v in enumerate(out for row in r['ambiguous_inputs'] for out in row['outputs'])}
        self.assertEqual(locations,json.loads(gzip.decompress((EVIDENCE/'locations.json.gz').read_bytes())))
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(len(r['ambiguous_inputs']),8)
        self.assertTrue(all(v['exact']<v['samples'] for v in r['scores'].values()))
        self.assertFalse(r['materialized_filter_input_proved'])
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
