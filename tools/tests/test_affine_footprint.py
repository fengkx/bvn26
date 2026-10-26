from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_affine_footprint import analyze, floor_surd

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r170'


class AffineFootprintTests(unittest.TestCase):
    def test_all_old_controls_without_per_pixel_routing(self):
        r = analyze(ROOT / 'evidence/importer-loud-fail')
        failures = {k: v.pop('failures') for k, v in r['scores'].items()}
        self.assertEqual(failures, json.loads(gzip.decompress((EVIDENCE / 'failures.json.gz').read_bytes())))
        self.assertEqual(r, json.loads((EVIDENCE / 'summary.json').read_text()))
        for family in ('fixed_inverse', 'fixed_inverse_offset'):
            rows = [v for k,v in r['scores'].items() if k.endswith('/'+family)]
            self.assertEqual(sum(v['exact'] for v in rows), 49309)
            self.assertTrue(all(v['exact'] == v['samples'] for v in rows))
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_exact_integer_boundary_and_negative_base(self):
        self.assertEqual(floor_surd(Fraction(-3,2), Fraction(9,4)), 0)
        self.assertEqual(floor_surd(Fraction(-3,2), Fraction(9,4)-Fraction(1,10**30)), -1)
        self.assertEqual(floor_surd(Fraction(-3,2), Fraction(9,4)+Fraction(1,10**30)), 0)

    def test_provenance(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
