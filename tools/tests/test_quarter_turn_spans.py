import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_quarter_turn_spans import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r135'


class QuarterTurnSpanTests(unittest.TestCase):
    def test_overlap_independently_requires_partition(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['source_pixels_exact'],32)
        self.assertEqual(r['overlapping_groups'],2790)
        self.assertEqual(len(r['changed_overlap']),157)
        rows=[v for k,v in r['scores'].items() if k.endswith('-byte')]
        self.assertEqual(sum(v['exact'] for v in rows),21354)
        self.assertEqual(sum(v['samples'] for v in rows),22604)
        self.assertFalse(r['interpolation_routing_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
