"""Protect complete structural comparison and the unproved execution boundary."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s291_diagnose', HERE / 'diagnose.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class CorrespondenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = json.loads((HERE.parent / 's283/diagnosis.json').read_text())

    def graphs(self):
        return (copy.deepcopy(self.prior['original_projection']),
                copy.deepcopy(self.prior['candidate_projection']))

    def test_complete_replay_keeps_proof_unknown(self):
        result = analysis.diagnose()
        self.assertEqual(result['historical_events_revalidated'], 5437)
        self.assertIsNone(result['historical_execution_observed'])
        for key in ('production_admitted', 'native_parity_proven', 'observer_qualified',
                    'activation_correspondence_proved', 'external_callsite_execution_proved'):
            self.assertIs(result[key], False)
        self.assertEqual(result['new_captures'], 0)

    def test_correspondence_accounts_for_every_node(self):
        a,b = self.graphs()
        report = analysis.audit(a,b)
        self.assertEqual(report['original_node_count'], report['residual_node_count'] + 2)
        self.assertEqual(report['candidate_node_count'], report['residual_node_count'] + 60)
        rows = report['node_correspondence']
        self.assertEqual(sum(r['instruction'] == 'Return' for r in rows), 6)
        self.assertEqual(sum(r['instruction'] == 'Push "hitTest"' for r in rows), 1)
        self.assertFalse(report['headers_equal'])
        self.assertEqual(len(report['assumptions_not_proved']), 4)

    def test_changed_branch_rejected(self):
        a,b = self.graphs()
        node = next(n for n in b['nodes'] if n['instruction'].startswith('If '))
        node['successors'][0] += 1
        with self.assertRaisesRegex(ValueError, 'control-flow mismatch'):
            analysis.audit(a,b)

    def test_changed_register_rejected(self):
        a,b = self.graphs()
        next(n for n in b['nodes'] if n['instruction'] == 'Push register3')['instruction'] = 'Push register4'
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            analysis.audit(a,b)

    def test_changed_original_write_rejected(self):
        a,b = self.graphs()
        next(n for n in a['nodes'] if n['instruction'] == 'SetMember')['instruction'] = 'SetVariable'
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            analysis.audit(a,b)

    def test_observer_envelope_change_rejected(self):
        a,b = self.graphs()
        next(n for n in b['nodes'] if n['instruction'] == 'Push "target"')['instruction'] = 'Push "other"'
        with self.assertRaisesRegex(ValueError, 'observer envelope'):
            analysis.audit(a,b)

    def test_erased_control_flow_cannot_be_hidden(self):
        a,b = self.graphs()
        node = next(n for n in b['nodes'] if n['instruction'] == 'Push register1')
        node['successors'] = [node['index'] + 2]
        with self.assertRaisesRegex(ValueError, 'erase control flow'):
            analysis.audit(a,b)

    def test_missing_initialization_rejected(self):
        a,b = self.graphs()
        next(n for n in b['nodes'] if n['instruction'] == 'StoreRegister 7')['instruction'] = 'StoreRegister 8'
        with self.assertRaisesRegex(ValueError, 'declaration envelope'):
            analysis.audit(a,b)

    def test_missing_return_rejected(self):
        a,b = self.graphs()
        next(n for n in b['nodes'] if n['instruction'] == 'Return')['instruction'] = 'Pop'
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            analysis.audit(a,b)

    def test_pins_reject_altered_input(self):
        with tempfile.TemporaryDirectory() as directory:
            pin = Path(directory)/'pins.json'
            pin.write_text(json.dumps({'evidence/sampling-upgrade/s283/original.pcode':'0'*64}))
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                analysis.verify_pins(pin)


if __name__ == '__main__':
    unittest.main()
