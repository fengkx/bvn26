"""Missing window binding cannot become native Button2009 behavior."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s352', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class BoundaryTests(unittest.TestCase):
    def test_complete_prior_replay(self):
        report = audit.diagnose()
        self.assertEqual(report['locked_s342_diagnosis'], json.loads((HERE.parent / 's342/diagnosis.json').read_text()))
        self.assertEqual(report['scope'], 'AFTER-s344 rank #8 only')
        self.assertEqual(report['constraints']['allowed_rank'], 8)
        for key in ('production_admitted', 'native_parity_proven', 'thin_coverage_cut_proved',
                    'native_ui_control_established', 'candidate_compiled',
                    'candidate_opcode_preservation_checked', 'ui_case_executed'):
            self.assertIs(report[key], False)
        self.assertTrue(all(value is None for value in report['observations'].values()))
        self.assertEqual(report['product_obligations_closed'], 0)

    def test_reject_invented_execution(self):
        original = json.loads((HERE / 'ui-control-attempts.json').read_text())
        changes = {'window_state_obtained': True, 'input_control_established': True,
                   'native_receipt': True, 'ui_inputs_sent': 1, 'instrumented_movie_launches': 1,
                   'new_capture_count': 1, 'app_activation_unknown': False,
                   'no_dispatch_observed': True, 'original_launch_requests': 0}
        for key, value in changes.items():
            with self.subTest(key=key):
                record = copy.deepcopy(original)
                record[key] = value
                with self.assertRaises(ValueError):
                    audit.audit_attempts(record)

    def test_observed_process_rows_are_not_windows(self):
        result = json.loads((HERE / 'bundle-window-result.json').read_text())
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['stdout'].count('pid=50810'), 2)
        self.assertNotIn('window=', result['stdout'])
        self.assertNotEqual(result['stdout'], 'matching_processes=0\n\n')


if __name__ == '__main__':
    unittest.main()
