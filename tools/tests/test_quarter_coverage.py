import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_quarter_coverage import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r139'


class QuarterCoverageTests(unittest.TestCase):
    def test_independent_quarter_grid_byte_coverage(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(len(r['inputs']),80)
        self.assertEqual(sum(v['exact'] for v in r['scores'].values()),163840)
        self.assertEqual(r['scores']['fringe']['exact'],26880)
        self.assertTrue(r['quarter_grid_constant_coverage_exact'])
        self.assertFalse(r['general_coverage_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
