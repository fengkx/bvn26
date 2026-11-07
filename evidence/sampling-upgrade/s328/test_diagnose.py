"""Reject facility substitutions and promotion of retained evidence to proof."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('s328_diagnose', Path(__file__).with_name('diagnose.py'))
D = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(D)


class FacilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {key: (D.ROOT / key.split('#')[0]).read_text() for key in D.FACILITIES}
        cls.result = D.diagnose()

    def test_source_spans_and_hashes(self):
        for row in D.facility_audit(self.sources):
            lines = (D.ROOT / row['path']).read_text().splitlines()
            self.assertEqual('\n'.join(lines[row['lines'][0]-1:row['lines'][1]]), row['source'])
            self.assertEqual(D.sha(row['source'].encode()), row['function_sha256'])
            self.assertFalse(row['invoked'])

    def test_register_read_substitution_rejected(self):
        sources = dict(self.sources)
        key = next(iter(sources))
        sources[key] = sources[key].replace('GetFrameAtIndex(0)', 'GetFrameAtIndex(1)')
        with self.assertRaises(ValueError):
            D.facility_audit(sources)

    def test_sample_duration_substitution_rejected(self):
        sources = dict(self.sources)
        key = 'tools/probes/monitor_owned_native.py#monitor_owned'
        sources[key] = sources[key].replace("str(pid),'1','1'", "str(pid),'2','1'")
        with self.assertRaises(ValueError):
            D.facility_audit(sources)

    def test_log_sequence_check_removal_rejected(self):
        sources = dict(self.sources)
        key = 'tools/sampling_native.py#validate_capture'
        sources[key] = sources[key].replace('sequence != list(range(1, len(sequence) + 1))', 'False')
        with self.assertRaises(ValueError):
            D.facility_audit(sources)

    def test_missing_facility_rejected(self):
        sources = dict(self.sources)
        sources.pop(next(iter(sources)))
        with self.assertRaises(ValueError):
            D.facility_audit(sources)

    def test_prior_proof_promotion_rejected(self):
        prior = D.load_prior().diagnose()
        prior['qualification_matrix'][0]['independent_entry'] = True
        with self.assertRaises(ValueError):
            D.validate_prior(prior)

    def test_full_prior_mismatch_rejected(self):
        prior = D.load_prior().diagnose()
        prior['new_images'] = 1
        with self.assertRaises(ValueError):
            D.validate_prior(prior)

    def test_all_frames_and_gates_remain_unproved(self):
        result = self.result
        for field in ('production_admitted', 'native_parity_proven', 'observer_qualified',
                      'independent_controls_proved', 'independent_child_clock_proved', 'fresh_capture_eligible'):
            self.assertIs(result[field], False)
        self.assertEqual([r['frame'] for r in result['qualification_matrix']], list(range(1, 11)))
        for row in result['qualification_matrix']:
            for field in ('independent_entry', 'isolated_repeated_target', 'isolated_changed_target',
                          'same_depth_replacement', 'observer_off_on_order'):
                self.assertIsNone(row[field])
        self.assertEqual(result['independent_observations_new'], [])
        self.assertEqual(result['other_ranks_executed'], [])
        self.assertIsNone(result['live_entry_resolver'])
        self.assertIsNone(result['live_instance_resolver'])


if __name__ == '__main__':
    unittest.main()
