"""Fixed affine orders retain signed controls and never borrow old-path bounds."""
import gzip
import json
from pathlib import Path
import unittest

from tools.probes.analyze_cxform_affine import affine


class AffineOrderTests(unittest.TestCase):
    def test_consumed_signed_and_clamped_operations(self):
        for form in ('unit_gain','premultiplied_gain'):
            self.assertEqual(affine((32,64,256,0,100),1/64,form),32)
            self.assertEqual(affine((32,64,-256,255,100),1/64,form),32)
            self.assertEqual(affine((32,64,256,0,50),1/64,form),16)
            self.assertEqual(affine((32,64,0,0,100),1/64,form),0)
            self.assertEqual(affine((32,64,-256,-255,100),1/64,form),0)
        with self.assertRaises(ValueError):
            affine((32,64,256,0,100),1/64,'pixel_selected')

    def test_pinned_global_rejection(self):
        path = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r50/analysis.json.gz'
        report = json.loads(gzip.decompress(path.read_bytes()))
        self.assertTrue(report['original_order_bounds_are_not_affine_bounds'])
        self.assertEqual(len(report['models']),14)
        for model in report['models'].values():
            self.assertTrue(any(v['native']!=v['actual'] for v in model['pair']))
            for group,total in (('old',1284192),('signed',18720)):
                score = model['scores'][group]
                self.assertEqual(score['total'],total)
                self.assertEqual(score['exact']+sum(v['count'] for v in score['failures']),total)
            self.assertTrue(model['scores']['old']['failures'])
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(report[flag])


if __name__=='__main__':
    unittest.main()
