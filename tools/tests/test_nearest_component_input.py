import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_nearest_component_input import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r179'

class NearestComponentInputTests(unittest.TestCase):
    def test_original_storage_and_transparent_interiors_remain_exact(self):
        r=analyze(EVIDENCE/'native');self.assertEqual(r.pop('failures'),[])
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(sum(v['interior']['indexed']['exact'] for v in r['rows']),52921)
        self.assertEqual([len(v['unproven_nonzero_pixels']) for v in r['rows']],[3,12])
        self.assertFalse(r['source_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
