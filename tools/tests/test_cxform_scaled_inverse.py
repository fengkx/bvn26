"""Paired native success is insufficient for scaled-inverse admission."""
import gzip
import json
from pathlib import Path
import unittest
from tools.probes.analyze_cxform_intervals import coefficient_measurements
from tools.probes.analyze_cxform_rejected import measurements
from tools.probes.analyze_cxform_scaled_inverse import evaluate, EVIDENCE


class ScaledInverseTests(unittest.TestCase):
    def test_independent_paired_construction(self):
        measured = coefficient_measurements(EVIDENCE/'r41')
        inverse = {a:v['estimate_inverse'] for a,v in measured.items()}
        table = measurements(EVIDENCE/'r44')['multiply_estimated']
        for args,target in (((25,49,-129,128,100),12),((23,49,2046,-894,100),11)):
            self.assertEqual(evaluate(args,table,inverse,'source_first'),target)
        with self.assertRaises(ValueError):
            evaluate((25,49,-129,128,100),table,inverse,'pixel_selected')

    def test_global_rejection_retains_all_controls(self):
        path = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r53/analysis.json.gz'
        r = json.loads(gzip.decompress(path.read_bytes()))
        self.assertEqual(len(r['models']),12)
        for model in r['models'].values():
            for group,total in (('old',1284192),('signed',18720)):
                score = model['scores'][group]
                self.assertEqual(score['total'],total)
                self.assertEqual(score['exact']+sum(v['count'] for v in score['failures']),total)
            self.assertTrue(model['scores']['old']['failures'])
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(r[flag])


if __name__=='__main__':
    unittest.main()
