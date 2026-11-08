"""Receipt joins and unproved dispatch must remain separate."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s361', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.facility = json.loads((HERE / 'facility-result.json').read_text())
        self.receipt = json.loads((HERE.parent / 's343/lookup-candidates.json').read_text())

    def test_complete_prior_replay(self):
        report = audit.diagnose()
        self.assertEqual(report['locked_s352_diagnosis'], json.loads((HERE.parent / 's352/diagnosis.json').read_text()))
        self.assertEqual(report['scope'], 'AFTER-s353 rank #8 only')
        for key in ('production_admitted', 'native_parity_proven', 'native_ui_control_established',
                    'candidate_compiled', 'candidate_opcode_preservation_checked', 'thin_coverage_cut_proved'):
            self.assertIs(report[key], False)
        self.assertTrue(all(value is None for value in report['observations'].values()))

    def test_process_path_and_owner_are_independent_joins(self):
        result = audit.associate(self.facility, self.receipt)
        self.assertEqual(result['pid'], 68944)
        self.assertEqual(result['window_number'], 117370)
        self.assertFalse(result['visible_content_proved'])
        for mutation in ('hash', 'ps', 'owner', 'duplicate', 'query'):
            record = copy.deepcopy(self.facility)
            state = json.loads(record['records'][1]['stdout'])
            if mutation == 'hash':
                record['observed_binary_sha256'] = '0' * 64
            elif mutation == 'ps':
                record['records'][0]['stdout'] = record['records'][0]['stdout'].replace('68944', '50810')
            elif mutation == 'owner':
                state['player_windows'][0]['kCGWindowOwnerPID'] = 50810
            elif mutation == 'duplicate':
                state['applications'].append(copy.deepcopy(state['applications'][1]))
            else:
                state['window_query_available'] = False
            record['records'][1]['stdout'] = json.dumps(state)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                audit.associate(record, self.receipt)

    def test_reject_invented_dispatch_and_input(self):
        original = json.loads((HERE / 'ui-control-attempts.json').read_text())
        for key, value in [('visible_window_proved', True), ('input_control_established', True),
                           ('native_dispatch_proved', True), ('ui_inputs_sent', 1),
                           ('original_launch_requests', 1), ('new_behavior_captures', 1),
                           ('candidate_compiled', True), ('no_dispatch_observed', True),
                           ('no_dispatch_observed', False)]:
            record = dict(original, **{key: value})
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                audit.audit_claims(record)


if __name__ == '__main__':
    unittest.main()
