"""Reject unsupported s265 placement and scene-admission claims."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s265'
SPEC = importlib.util.spec_from_file_location('s265_diagnosis', HERE / 'diagnose.py')
diag = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diag)


class CallbackSceneLifetimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = diag.s262.s258.s253.events_from(gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode().splitlines())

    def test_retained_evidence(self):
        result = diag.diagnose()
        self.assertEqual(result, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual(result['actor_rows_equal_s262'], 122)
        self.assertEqual(result['images_written'], 0)
        self.assertTrue(result['no_encoding']['bounded_no_encoding_lifetime_observed'])
        for flag in ('production_admitted', 'native_parity_proven', 'thin_state_admission_proved', 'encoded_lifetime_join_proved', 'common_visual_phase_proved', 'scene_join_attempted'):
            self.assertFalse(result[flag])

    def test_frame1_entry_cannot_replace_load(self):
        events = [e for e in self.events if not (e['kind'] == 's265_life' and '.个,' in e['value'])]
        with self.assertRaisesRegex(ValueError, 'placement load'):
            diag.analyze(events)

    def test_missing_replacement_control_rejects(self):
        events = [e for e in self.events if not (e['kind'] == 's265_life' and '100001,3,' in e['value'])]
        with self.assertRaisesRegex(ValueError, 'lifecycle controls'):
            diag.analyze(events)

    def test_changed_sample_generation_rejects(self):
        events = copy.deepcopy(self.events)
        event = next(e for e in events if e['kind'] == 's265_state' and e['tick'] == 13)
        values = event['value'].split(',')
        values[3] = '2'
        event['value'] = ','.join(values)
        with self.assertRaisesRegex(ValueError, 'sample generation'):
            diag.analyze(events)

    def test_missing_target_entry_rejects(self):
        events = [e for e in self.events if not (e['kind'] == 's265_entry' and e['tick'] == 1)]
        with self.assertRaisesRegex(ValueError, 'target-frame entry'):
            diag.analyze(events)

    def test_missing_terminal_sample_rejects(self):
        events = [e for e in self.events if not (e['kind'] == 's265_state' and e['tick'] == 60)]
        with self.assertRaisesRegex(ValueError, 'sample boundary'):
            diag.analyze(events)

    def test_images_before_admission_reject(self):
        with self.assertRaisesRegex(ValueError, 'images before'):
            diag.analyze(self.events + [{'kind': 'bitmap_begin'}])

    def test_missing_no_encoding_boundary_rejects(self):
        events = copy.deepcopy(self.events)
        event = next(e for e in events if e['kind'] == 's265_no_encoding' and e['tick'] == 1 and e['value'] == 'after')
        event['kind'] = 'unbound'
        with self.assertRaisesRegex(ValueError, 'no-encoding completion'):
            diag.analyze(events)


if __name__ == '__main__':
    unittest.main()
