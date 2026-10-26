import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_integer_filter_extent import analyze, extent

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r69'


class IntegerFilterExtentTests(unittest.TestCase):
    def test_all_old_and_new_controls_pass_without_production_admission(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r['prior_implicit']['exact'], 85120)
        self.assertEqual(r['new_explicit']['exact'], 30720)
        for stage in ('filtered', 'final'):
            self.assertEqual(r['new_native_comparisons'][stage]['exact'], 30720)
        self.assertTrue(r['bounded_native_controls_passed'])
        self.assertFalse(r['production_admitted'])

    def test_unproven_fractional_inputs_fail_instead_of_truncating(self):
        for args in ((17, 40.5, 5), (17.5, 40, 5), (17, 40, -1), (17, float('inf'), 5)):
            with self.assertRaises(ValueError):
                extent(*args)

    def test_sources_and_old_rejection_constraints_are_pinned(self):
        provenance = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', EVIDENCE / 'native'),
                          ('output_sha256', EVIDENCE)]:
            for name, digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
