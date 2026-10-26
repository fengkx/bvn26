import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_nearest_cache_local import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r193'

class NearestCacheLocalTests(unittest.TestCase):
    def test_local_cache_and_bounded_final_wrapper_exact(self):
        r=analyze(ROOT/'evidence/importer-loud-fail/r192/native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        for row in r['synthetic']:
            self.assertEqual(row['indexed']['exact'],240000)
            self.assertEqual(row['materialized']['exact'],240000)
        for row in r['original']['rows']:
            for comparison in row['comparisons'].values():self.assertEqual(comparison['exact'],240000)
        self.assertFalse(r['original']['matrix_rgb_intermediate_proved'])
        self.assertFalse(r['general_cache_initializer_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
