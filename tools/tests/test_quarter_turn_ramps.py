import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_quarter_turn_ramps import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r134'


class QuarterTurnRampTests(unittest.TestCase):
    def test_signed_initializer_is_bounded_not_globally_admitted(self):
        for native,file,exact in [(EVIDENCE/'native','summary.json',21522),(ROOT/'evidence/importer-loud-fail/r133/native','transparent-rejection.json',21206)]:
            result=analyze(native)
            self.assertEqual(result,json.loads((EVIDENCE/file).read_text()))
            scores=[v for k,v in result['scores'].items() if k.endswith('-byte')]
            self.assertEqual(sum(v['exact'] for v in scores),exact)
            self.assertEqual(sum(v['samples'] for v in scores),22224)
            for k,v in result['scores'].items():
                if k.endswith('-byte') and (k.startswith('turn1-') or k.startswith('turn3-')):
                    self.assertEqual(v['exact'],v['samples'])
            self.assertFalse(result['initializer_admitted'])
            self.assertFalse(result['interpolation_routing_admitted'])
            self.assertFalse(result['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
