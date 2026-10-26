import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_nearest_affine_intervals import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r160'

class NearestAffineIntervalTests(unittest.TestCase):
    def test_intervals_reject_all_independent_constructions(self):
        r=analyze(ROOT/'evidence/importer-loud-fail/r158/native');intervals=r.pop('intervals')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(intervals,json.loads(gzip.decompress((EVIDENCE/'intervals.json.gz').read_bytes())))
        self.assertEqual(r['source_index_constraints'],44522)
        for score in r['coefficient_feasibility'].values():self.assertEqual(score,{'intervals':320,'feasible':320})
        for score in r['construction_scores'].values():self.assertLess(score['inside'],score['intervals'])
        self.assertFalse(r['coefficients_selected_from_intervals'])
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
