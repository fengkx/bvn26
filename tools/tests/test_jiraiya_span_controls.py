import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_jiraiya_span_controls import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r90'


class JiraiyaSpanControlTests(unittest.TestCase):
    def test_single_pixel_controls_reject_routing_only_explanation(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(r['input_exact'],41760)
        self.assertEqual((r['interior_old_model']['exact'],r['interior_old_model']['samples']),(9045,9360))
        self.assertEqual((r['coordinate_compatible_groups'],r['groups']),(1455,1560))
        bad=[x for x in r['mode_compatibility'] if not x['compatible_modes']]
        self.assertEqual(len(bad),105)
        self.assertTrue(all(x['key'][0]==4 and x['key'][-2]==75 for x in bad))
        self.assertEqual(sum(x['key'][1]==1 for x in bad),5)
        self.assertEqual(r['clip_dependent_overlap_groups'],283)
        self.assertFalse(r['routing_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_native_source_inputs_and_old_arithmetic_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
