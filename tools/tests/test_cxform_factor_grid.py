"""A fixed complete grid must preserve prior controls and global rejection."""
import gzip
import itertools
import json
from pathlib import Path
import unittest
from tools.probes.analyze_cxform_intervals import CONSTRUCTIONS


class FactorGridTests(unittest.TestCase):
    def test_complete_grid_and_r53_retention(self):
        root = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail'
        new = json.loads(gzip.decompress((root/'r54/analysis.json.gz').read_bytes()))
        old = json.loads(gzip.decompress((root/'r53/analysis.json.gz').read_bytes()))
        expected = {'/'.join(v) for v in itertools.product(CONSTRUCTIONS,
            ('divide','multiply_rounded','multiply_estimated'),('source_first','gain_first'))}
        self.assertEqual(set(new['models']),expected)
        for name,model in old['models'].items():
            self.assertEqual(new['models'][name]['scores'],model['scores'])
            self.assertEqual(new['models'][name]['sites'][:2],model['pair'])

    def test_all_controls_retained_and_no_admission(self):
        path = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r54/analysis.json.gz'
        r = json.loads(gzip.decompress(path.read_bytes()))
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
