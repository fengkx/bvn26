import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_clipped_half_step import analyze
from tools.probes.bitmap_half_even_candidate import old_controls,jiraiya_controls,span_controls

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r91'


class ClippedHalfStepTests(unittest.TestCase):
    def test_independent_scalar_rules(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(r['input_exact'],2528)
        self.assertEqual(r['passed_scalar_rules'],['even'])
        self.assertEqual(r['scores']['even']['exact'],16377)
        self.assertEqual(r['scores']['ceiling']['exact'],16359)
        self.assertEqual(r['scores']['floor']['exact'],16358)
        self.assertFalse(r['production_admitted'])

    def test_common_rule_retains_old_and_independent_controls(self):
        r={'old':old_controls(),'jiraiya':jiraiya_controls(),'spans':span_controls(),'production_admitted':False}
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'heldout.json.gz').read_bytes())))
        self.assertEqual(r['old']['exact'],71824)
        self.assertEqual(r['jiraiya']['exact_images'],6)
        self.assertEqual(r['spans']['exact'],9360)

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
