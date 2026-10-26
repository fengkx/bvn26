import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_matrix_offset_brackets import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r203'

class MatrixOffsetBracketsTests(unittest.TestCase):
    def test_explicit_inputs_and_rejected_common_arithmetic(self):
        r=analyze(EVIDENCE/'native',ROOT/'evidence/importer-loud-fail/r202/native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'summary.json.gz').read_bytes())))
        self.assertEqual(r['source_pixels_exact'],19440)
        self.assertEqual(r['identity_other_channels_exact'],4860)
        for score in r['candidates'].values():self.assertLess(score['exact_red'],score['samples'])
        self.assertEqual(r['retained_zero_offset_cases'],540)
        self.assertEqual(sum(v['equal_zero_offset'] and not v['equal_all_offsets'] for v in r['coefficient_equivalence']),56)
        self.assertFalse(r['arithmetic_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
