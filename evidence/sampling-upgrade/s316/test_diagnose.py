"""Protect fixed replay provenance and prevent source signals becoming native proof."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s316', HERE / 'diagnose.py')
s316 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s316)


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = json.loads((HERE.parent / 's307/diagnosis.json').read_text())
        with gzip.open(HERE.parent / 's261/native-capture.log.gz', 'rt') as stream:
            cls.raw = stream.read()

    def audit(self, raw=None, source=None):
        return s316.audit_controls(self.raw if raw is None else raw,
                                   self.prior['source_audit'] if source is None else source)

    def test_replay_and_no_admission(self):
        report = s316.diagnose()
        self.assertEqual(report['locked_s307_diagnosis'], self.prior)
        for key in ('production_admitted', 'native_parity_proven', 'slot_reference_proved',
                    'content_clearing_proved', 'replacement_proved', 'allocation_identity_proved',
                    'actual_native_controls_executed'):
            self.assertIs(report[key], False)
        self.assertTrue(all(v is None for v in report['native_observations'].values()))

    def test_boolean_collision_has_different_operands(self):
        audit = self.audit()
        self.assertFalse(audit['equal_boolean_signals']['same_reference_operands'])
        bindings = audit['control_bindings']
        self.assertEqual([b['operands']['left_reference'] for b in bindings], ['saved', 'saved', 'retained'])
        self.assertTrue(all(b['independent_native_referents'] is None for b in bindings))

    def test_creation_and_cleanup_are_unbracketed(self):
        intervals = self.audit()['unobserved_native_intervals']
        self.assertEqual([r['bracketing_control_sequences'] for r in intervals],
                         [[None, 21], [21, 22], [22, 23], [23, None]])
        self.assertTrue(all(r['native_pool_events'] is None for r in intervals))
        self.assertTrue(all(not r['native_generation_order_proved'] for r in intervals))

    def test_retains_complete_root_window(self):
        rows = self.audit()['root8_root9_window']
        self.assertEqual([{k: v for k, v in r.items() if k != 'run'} for r in rows],
                         self.prior['reference_window']['events'])

    def test_missing_event_rejected(self):
        lines = self.raw.splitlines()
        del lines[21]
        with self.assertRaises(ValueError):
            self.audit('\n'.join(lines))

    def test_reordered_events_rejected(self):
        lines = self.raw.splitlines()
        lines[21], lines[22] = lines[22], lines[21]
        with self.assertRaises(ValueError):
            self.audit('\n'.join(lines))

    def test_cross_run_rejected(self):
        with self.assertRaises(ValueError):
            self.audit(self.raw.replace('s261-yijiao-r01', 'other-run', 1))

    def test_deleted_property_cannot_be_renamed_content_clear(self):
        with self.assertRaises(ValueError):
            self.audit(self.raw.replace('retained_content_deleted,true,false', 'content_cleared,true,false'))

    def test_changed_reference_operand_rejected(self):
        source = copy.deepcopy(self.prior['source_audit'])
        source['control_logs'][2]['statement'] = source['control_logs'][2]['statement'].replace('retained ==', 'saved ==')
        with self.assertRaises(ValueError):
            self.audit(source=source)

    def test_logger_continuity_is_not_pool_coverage(self):
        audit = self.audit()
        self.assertTrue(audit['as2_sequence_contiguous'])
        self.assertFalse(audit['uninterrupted_native_pool_coverage'])
        self.assertFalse(audit['independent_native_layouts_derived'])


if __name__ == '__main__':
    unittest.main()
