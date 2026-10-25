import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_twip_coverage import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r152'

class TwipCoverageTests(unittest.TestCase):
    def test_geometry_quantization_and_rejected_ideal_area(self):
        r=analyze(EVIDENCE/'native');failures=r.pop('failures')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(failures,json.loads(gzip.decompress((EVIDENCE/'failures.json.gz').read_bytes())))
        self.assertEqual(r['quarter_rounded_geometry']['all'],{'samples':153600,'exact':153600,'max_channel_delta':0})
        self.assertEqual(r['scores']['fringe']['max_channel_delta'],49)
        self.assertFalse(r['general_coverage_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
