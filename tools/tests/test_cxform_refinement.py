"""Construction definitions must be independent of native feasibility intervals."""
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.probes import analyze_cxform_refinement as probe


class ReciprocalRefinementTests(unittest.TestCase):
    def test_definitions_do_not_read_bounds(self):
        with patch.object(probe,'load_bounds',side_effect=AssertionError('Fitted coefficient')):
            tables = probe.constructions()
        self.assertEqual(len(tables),10)
        for table in tables.values():
            self.assertEqual(set(table),set(range(1,256)))
            self.assertTrue(all(value>0 for value in table.values()))

    def test_fixed_refinement_and_invalid_form(self):
        for form in ('product','residual'):
            self.assertEqual(probe.refine(4.0,0.25,form),0.25)
            self.assertEqual(probe.refine(4.0,0.125,form),0.1875)
        with self.assertRaises(ValueError):
            probe.refine(4.0,0.25,'selected')

    def test_evidence_retains_every_control_and_rejection(self):
        path = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r49/analysis.json.gz'
        report = json.loads(gzip.decompress(path.read_bytes()))
        self.assertEqual(report['older_upper_witness']['args'],[23,49,2046,-894,100])
        for value in report['constructions'].values():
            self.assertEqual(len(value['models']),9)
            for model in value['models'].values():
                self.assertTrue(model['outside_alphas'])
                for group,total in (('old',1284192),('signed',18720)):
                    score = model['scores'][group]
                    self.assertEqual(score['total'],total)
                    self.assertEqual(score['exact']+sum(v['count'] for v in score['failures']),total)
                self.assertEqual(model['pair'][0]['args'],[25,49,-129,128,100])
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(report[flag])


if __name__=='__main__':
    unittest.main()
