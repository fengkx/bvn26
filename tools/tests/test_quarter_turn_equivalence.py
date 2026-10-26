import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_quarter_turn_equivalence import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r133'


class QuarterTurnEquivalenceTests(unittest.TestCase):
    def test_native_permutation_counterexamples_remain_closed(self):
        result=analyze(EVIDENCE/'native')
        self.assertEqual(json.loads(json.dumps(result)),json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(result['permutation_bytes_exact'],48)
        self.assertEqual(sum(g['exact_pairs'] for g in result['groups'].values()),162)
        self.assertEqual(sum(g['exact_pixels'] for g in result['groups'].values()),217324)
        self.assertFalse(result['quarter_turn_equivalence_admitted'])
        self.assertFalse(result['production_admitted'])
        for name in ('turn0-cachefalse','turn0-cachetrue'):
            self.assertEqual(result['groups'][name]['exact_pairs'],36)

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
