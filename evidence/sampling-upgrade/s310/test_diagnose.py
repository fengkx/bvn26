"""Protect historical witness custody and the unproved live-observer boundary."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('s310', HERE / 'diagnose.py')
s310 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s310)


class WitnessTests(unittest.TestCase):
    def setUp(self):
        self.audit = json.loads((HERE.parent / 's292/diagnosis.json').read_text())['control_audit']

    def test_locked_replay_and_unknowns(self):
        result = s310.diagnose()
        self.assertTrue(result['locked_s301_reproduced'])
        self.assertEqual(result['m0_02_status'], 'pending')
        for field in ('production_admitted', 'native_parity_proven', 'observer_qualified',
                      'independent_controls_proved', 'independent_child_clock_proved', 'fresh_capture_eligible'):
            self.assertIs(result[field], False)
        for row in result['qualification_matrix']:
            for field in ('independent_entry', 'isolated_repeated_target', 'isolated_changed_target',
                          'same_depth_replacement', 'observer_off_on_order'):
                self.assertIsNone(row[field])
        self.assertEqual(result['new_captures'], 0)
        self.assertEqual(result['other_ranks_executed'], [])

    def test_replacement_witnesses_keep_actual_depths(self):
        rows = s310.replacement_audit(self.audit)
        self.assertEqual([[r[k]['sequence'] for k in ('before', 'unload', 'load', 'after')] for r in rows],
                         [[21737, 21783, 21784, 21831], [22114, 22168, 22169, 22218]])
        for row in rows:
            self.assertEqual(row['unload_state']['depth'], -132770)
            self.assertEqual(row['endpoint_states'][0]['depth'], 100001)
            self.assertEqual(row['observed_helper_frames'], [1])
            self.assertEqual(row['explicit_target_selection_count'], 0)
            self.assertIsNone(row['live_instance_identity'])
            self.assertFalse(row['unload_depth_equals_endpoint'])

    def test_cross_run_rejected(self):
        self.audit['historical_lifecycle_events'][1]['run'] = 'other'
        with self.assertRaisesRegex(ValueError, 'cross-run'):
            s310.replacement_audit(self.audit)

    def test_missing_or_duplicate_lifecycle_rejected(self):
        for duplicate in (False, True):
            audit = copy.deepcopy(self.audit)
            if duplicate:
                audit['historical_lifecycle_events'].append(copy.deepcopy(audit['historical_lifecycle_events'][1]))
            else:
                audit['historical_lifecycle_events'].pop(1)
            with self.assertRaises(ValueError):
                s310.replacement_audit(audit)

    def test_reversed_lifecycle_rejected(self):
        events = self.audit['historical_lifecycle_events']
        events[1]['sequence'], events[2]['sequence'] = events[2]['sequence'], events[1]['sequence']
        with self.assertRaisesRegex(ValueError, 'order'):
            s310.replacement_audit(self.audit)

    def test_wrong_generation_rejected(self):
        self.audit['historical_lifecycle_events'][1]['value'] = self.audit['historical_lifecycle_events'][1]['value'].replace(',2,1', ',9,1')
        with self.assertRaisesRegex(ValueError, 'identity'):
            s310.replacement_audit(self.audit)

    def test_wrong_frame_or_path_or_depth_rejected(self):
        for value in ('load,other,100001,3,1',
                      'load,_level0.xuetiao.instance76.instance77.__s274Control,100002,3,1',
                      'load,_level0.xuetiao.instance76.instance77.__s274Control,100001,3,2'):
            audit = copy.deepcopy(self.audit)
            audit['historical_lifecycle_events'][2]['value'] = value
            with self.assertRaisesRegex(ValueError, 'identity/frame'):
                s310.replacement_audit(audit)

    def test_selection_added_to_replacement_rejected(self):
        self.audit['groups']['replacement']['source'] += '\ntimer.__s274Control.gotoAndStop(10);'
        with self.assertRaisesRegex(ValueError, 'source'):
            s310.replacement_audit(self.audit)

    def test_endpoint_run_rejected(self):
        self.audit['historical_boundaries']['replace_after']['run'] = 'other'
        with self.assertRaisesRegex(ValueError, 'run/order'):
            s310.replacement_audit(self.audit)

    def test_all_cli_gates_fail_honestly(self):
        with tempfile.TemporaryDirectory() as directory:
            for flag, code in s310.GATES.items():
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'),
                                         '--output', str(Path(directory) / 'result.json'),
                                         '--require-' + flag], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stdout)


if __name__ == '__main__':
    unittest.main()
