import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_matrix_component_boundaries import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r157'

class MatrixComponentBoundaryTests(unittest.TestCase):
    def test_native_properties_clocks_and_direct_composition(self):
        for name in ('main','yijiao'):
            r=analyze(EVIDENCE/name)
            self.assertEqual(json.loads(json.dumps(r)),json.loads((EVIDENCE/(name+'-summary.json')).read_text()))
            for row in r['rows']:self.assertEqual(row['pinned']['exact'],240000)
            self.assertFalse(r['source_sampler_admitted'])
            self.assertFalse(r['production_admitted'])
            if name=='yijiao':
                self.assertEqual(r['rows'][0]['cache_vs_authored']['exact'],240000)
                self.assertLess(r['rows'][0]['normal_composite_vs_stage']['exact'],240000)

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
