import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_quarter_turn_heldout import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r137'


class QuarterTurnHeldoutTests(unittest.TestCase):
    def test_fixed_construction_retains_distant_signed_controls(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['scores']['horizontal']['exact'],155624)
        self.assertEqual(r['scores']['horizontal']['samples'],155624)
        self.assertEqual(r['scores']['vertical']['exact'],110526)
        self.assertFalse(r['partition_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
