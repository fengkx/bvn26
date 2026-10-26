import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_nearest_affine_distant import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r163'

class NearestAffineAxisTests(unittest.TestCase):
    def test_distant_input_constraints_retain_initializer_rejection(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['source_texels_exact'],16384)
        self.assertEqual(r['scores']['exact_inverse_center']['exact'],576)
        self.assertEqual(r['scores']['fixed_inverse_center']['exact'],608)
        for score in r['coefficient_feasibility'].values():self.assertEqual(score,{'intervals':80,'feasible':80})
        self.assertFalse(r['coefficients_selected_from_intervals'])
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
