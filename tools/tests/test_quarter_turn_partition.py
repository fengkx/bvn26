import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_quarter_turn_partition import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r136'


class QuarterTurnPartitionTests(unittest.TestCase):
    def test_one_geometry_partition_distinguishes_operation_order(self):
        for native,file,ramps in [(ROOT/'evidence/importer-loud-fail/r135/native','ramps-partition.json',True),(EVIDENCE/'native','summary.json',False)]:
            r=analyze(native,ramps)
            self.assertEqual(r,json.loads((EVIDENCE/file).read_text()))
            self.assertEqual(r['scores']['horizontal']['exact'],22604)
            self.assertEqual(r['scores']['horizontal']['samples'],22604)
            self.assertEqual(r['scores']['vertical']['exact'],22604 if ramps else 18819)
            self.assertFalse(r['partition_admitted'])
            self.assertFalse(r['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
