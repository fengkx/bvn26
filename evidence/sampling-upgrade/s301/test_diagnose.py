"""Source-bound negatives for the state-to-entry qualification boundary."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('s301', HERE / 'diagnose.py')
s301 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s301)


class FacilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = json.loads((HERE.parent / 's292/diagnosis.json').read_text())

    def test_replay_preserves_unknowns(self):
        result = s301.diagnose()
        self.assertEqual(result['historical'], self.prior['historical'])
        self.assertEqual(len(result['unobserved_frame1_windows']), 14)
        for row in result['unobserved_frame1_windows']:
            self.assertIsNone(row['independent_target_entry_observed'])
        for key in ('production_admitted', 'native_parity_proven', 'observer_qualified',
                    'independent_child_clock_proved'):
            self.assertIs(result[key], False)
        for row in result['qualification_matrix']:
            for key in ('independent_entry', 'isolated_repeated_target',
                        'isolated_changed_target', 'same_depth_replacement', 'observer_off_on_order'):
                self.assertIsNone(row[key])
        self.assertEqual(result['new_captures'], 0)

    def test_all_ten_glyphs_do_not_supply_live_clock(self):
        rows = s301.placement_inventory(self.prior['byte_audit']['original_tags'])
        self.assertEqual([r['symbol'] for r in rows], list(range(1800, 1810)))
        self.assertEqual([r['move'] for r in rows], [False] + [True] * 9)
        self.assertTrue(all(not r['has_clip_actions'] for r in rows))

    def test_missing_frame_rejected(self):
        tags = copy.deepcopy(self.prior['byte_audit']['original_tags'])
        tags = [r for r in tags if r['frame'] != 10]
        with self.assertRaisesRegex(ValueError, 'inventory'):
            s301.placement_inventory(tags)

    def test_changed_move_character_depth_or_clip_action_rejected(self):
        for payload in ('0201000907', '0302000907', '0301000807', '8301000907', '010100'):
            with self.subTest(payload=payload):
                tags = copy.deepcopy(self.prior['byte_audit']['original_tags'])
                next(r for r in tags if r['frame'] == 2 and r['code'] == 26)['payload_hex'] = payload
                with self.assertRaises(ValueError):
                    s301.placement_inventory(tags)

    def test_equal_endpoints_are_not_no_entry(self):
        rows = s301.control_sequences(self.prior['control_audit'])
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertTrue(row['endpoint_state_equal'])
            self.assertLess(row['after']['sequence'], row['later_entry']['sequence'])
            self.assertIsNone(row['intermediate_frame2_entry'])
            self.assertIsNone(row['isolated_repeated_target_entry'])

    def test_repeated_target_relabel_rejected(self):
        audit = copy.deepcopy(self.prior['control_audit'])
        audit['groups']['retained']['source'] = audit['groups']['retained']['source'].replace('gotoAndStop(2)', 'gotoAndStop(1)')
        with self.assertRaisesRegex(ValueError, 'call sequence'):
            s301.control_sequences(audit)

    def test_cross_run_join_rejected(self):
        audit = copy.deepcopy(self.prior['control_audit'])
        audit['historical_retained_entries'][0]['run'] = 'other'
        with self.assertRaisesRegex(ValueError, 'cross-run'):
            s301.control_sequences(audit)

    def test_entry_order_rejected(self):
        audit = copy.deepcopy(self.prior['control_audit'])
        audit['historical_retained_entries'][0]['sequence'] = 21647
        with self.assertRaisesRegex(ValueError, 'order'):
            s301.control_sequences(audit)

    def test_missing_or_duplicate_entry_rejected(self):
        for entries in ([], [self.prior['control_audit']['historical_retained_entries'][0]] * 2):
            audit = copy.deepcopy(self.prior['control_audit'])
            audit['historical_retained_entries'] = entries
            with self.assertRaisesRegex(ValueError, 'ambiguous'):
                s301.control_sequences(audit)

    def test_instance_generation_mismatch_rejected(self):
        audit = copy.deepcopy(self.prior['control_audit'])
        audit['historical_retained_entries'][0]['value'] = audit['historical_retained_entries'][0]['value'].replace(',2,1', ',3,1')
        with self.assertRaisesRegex(ValueError, 'identity'):
            s301.control_sequences(audit)


if __name__ == '__main__':
    unittest.main()
