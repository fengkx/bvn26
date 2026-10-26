import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_mask_coverage import analyze,decode
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r181'

class AffineMaskCoverageTests(unittest.TestCase):
    def test_native_storage_agreement_keeps_coverage_rejected(self):
        r=analyze(EVIDENCE/'native');f={k:v.pop('failures') for k,v in r['scores'].items()}
        self.assertEqual(f,json.loads(gzip.decompress((EVIDENCE/'failures.json.gz').read_bytes())))
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(sum(v['exact'] for v in r['storage_pairs']),80675)
        self.assertEqual(r['scores']['lower_consumed']['exact'],158512)
        self.assertFalse(r['coverage_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_incomplete_roi_is_rejected_before_arithmetic(self):
        with self.assertRaisesRegex(ValueError,'case_0: capture ROI excludes native nonzero bounds'):
            decode(EVIDENCE/'invalid-roi')

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
