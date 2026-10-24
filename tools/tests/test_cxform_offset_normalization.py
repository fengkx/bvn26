"""Offset hypotheses must retain independent zero-source native controls."""
import gzip
import json
from pathlib import Path
import unittest

from tools.probes.analyze_cxform_intervals import f32
from tools.probes.analyze_cxform_offset_normalization import evaluate


class OffsetNormalizationTests(unittest.TestCase):
    def test_zero_source_and_invalid_order(self):
        for form in ('source_first','unit_gain','premultiplied_gain'):
            self.assertEqual(evaluate((0,64,-129,255,100),1/64,f32(1/255),form),64)
            self.assertEqual(evaluate((0,64,129,-255,100),1/64,f32(1/255),form),0)
            self.assertEqual(evaluate((32,64,-256,255,100),1/64,f32(1/255),form),32)
        with self.assertRaises(ValueError):
            evaluate((0,64,128,128,100),1/64,f32(1/255),'pixel_selected')

    def test_all_native_groups_retained(self):
        path = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r51/analysis.json.gz'
        report = json.loads(gzip.decompress(path.read_bytes()))
        self.assertEqual(len(report['models']),42)
        self.assertTrue(report['old_bounds_retained_not_reinterpreted'])
        for model in report['models'].values():
            for group,total in (('old',1284192),('signed',18720),('pure_offset_green',3840)):
                score = model['scores'][group]
                self.assertEqual(score['total'],total)
                self.assertEqual(score['exact']+sum(v['count'] for v in score['failures']),total)
            self.assertTrue(model['scores']['old']['failures'])
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(report[flag])


if __name__=='__main__':
    unittest.main()
