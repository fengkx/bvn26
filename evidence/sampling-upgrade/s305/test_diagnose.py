"""Keep facility failures distinct from observed native button behavior."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s305', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class NativeUIBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((HERE / 'ui-control-attempts.json').read_text())

    def test_replay_does_not_promote_inventory_or_source_patches(self):
        report = audit.diagnose()
        for key in ('production_admitted', 'native_parity_proven', 'thin_coverage_cut_proved',
                    'native_ui_control_established', 'candidate_compiled',
                    'candidate_opcode_preservation_checked', 'ui_case_executed'):
            self.assertIs(report[key], False)
        self.assertTrue(all(value is None for value in report['observations'].values()))
        self.assertEqual(report['historical_s263_replay']['events'], 9774)
        self.assertEqual(report['historical_s263_replay']['strict_full_as_exit'], 1)
        self.assertEqual(len(report['family_obligations']), 2)

    def test_new_input_or_window_requires_new_analysis(self):
        for key in ('ui_inputs_sent', 'instrumented_movie_launches', 'new_capture_count'):
            record = copy.deepcopy(self.record)
            record[key] = 1
            with self.assertRaisesRegex(ValueError, 'independent analysis'):
                audit.audit_attempts(record)
        self.record['attempts'][-1]['window_state_obtained'] = True
        with self.assertRaisesRegex(ValueError, 'independent analysis'):
            audit.audit_attempts(self.record)

    def test_facility_result_cannot_become_receipt(self):
        self.record['native_receipt'] = True
        with self.assertRaisesRegex(ValueError, 'not a native receipt'):
            audit.audit_attempts(self.record)

    def test_activation_cannot_be_assumed_absent(self):
        self.record['app_activation_unknown'] = False
        with self.assertRaisesRegex(ValueError, 'activation proof'):
            audit.audit_attempts(self.record)

    def test_timeout_is_required(self):
        self.record['attempts'][0]['result'] = 'success'
        with self.assertRaisesRegex(ValueError, 'missing retained'):
            audit.audit_attempts(self.record)

    def test_wrong_app_cannot_qualify(self):
        self.record['attempts'][0]['operation'] = 'await cua.getState();'
        with self.assertRaisesRegex(ValueError, 'exact installed path'):
            audit.audit_attempts(self.record)

    def test_invalid_cost_rejected(self):
        for value in (-1, float('nan'), float('inf')):
            self.record['attempts'][0]['reported_wall_seconds'] = value
            with self.assertRaisesRegex(ValueError, 'invalid measured'):
                audit.audit_attempts(self.record)

    def test_locked_s296_reproduced_in_full(self):
        report = audit.diagnose()
        expected = json.loads((HERE.parent / 's296/diagnosis.json').read_text())
        self.assertEqual(report['locked_s296_diagnosis'], expected)
        self.assertEqual(report['scope'], 'AFTER-s299 rank #6 only')
        self.assertEqual(report['product_obligations_closed'], 0)
        self.assertEqual(report['constraints']['allowed_rank'], 6)
        self.assertTrue(all(value is False for key, value in report['constraints'].items()
                            if key != 'allowed_rank'))

    def test_cost_preserves_all_attempts(self):
        self.assertAlmostEqual(audit.audit_attempts(self.record), 18.3654)


if __name__ == '__main__':
    unittest.main()
