import gzip
import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_affine_heldout import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r171'


class AffineHeldoutTests(unittest.TestCase):
    def test_reflection_counterexamples_keep_admission_closed(self):
        r = analyze(EVIDENCE / 'native')
        failures = {k:v.pop('failures') for k,v in r['scores'].items()}
        self.assertEqual(failures,json.loads(gzip.decompress((EVIDENCE / 'failures.json.gz').read_bytes())))
        self.assertEqual(r,json.loads((EVIDENCE / 'summary.json').read_text()))
        self.assertEqual(r['scores']['positive/fixed_inverse']['exact'],1024)
        self.assertEqual(r['scores']['reflected/fixed_inverse']['exact'],624)
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE / 'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
