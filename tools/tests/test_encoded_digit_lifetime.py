"""Keep s274 lifetime evidence separate from complete state admission."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s274'
SPEC = importlib.util.spec_from_file_location('s274_diagnosis', HERE / 'diagnose.py')
diag = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diag)


class EncodedDigitLifetimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = diag.events_from(gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()))

    def changed(self, kind, prefix, value=None):
        events = copy.deepcopy(self.events)
        event = next(e for e in events if e['kind'] == kind and e['value'].startswith(prefix))
        if value is None:
            event['kind'] = 'removed_observation'
        else:
            event['value'] = value
        return events

    def test_retained_evidence(self):
        result = diag.diagnose()
        self.assertEqual(result, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual(result['actor_rows_equal_s265'], 122)
        self.assertEqual(result['images_written'], 0)
        for flag in ('production_admitted', 'native_parity_proven', 'thin_state_admission_proved',
                     'common_visual_phase_proved', 'scene_state_admitted', 'scene_join_attempted'):
            self.assertFalse(result[flag])

    def test_entry_is_not_birth(self):
        with self.assertRaisesRegex(ValueError, 'load interval'):
            diag.analyze(self.changed('s274_life', 'load,_level0.xuetiao'))

    def test_control_load_missing(self):
        events = copy.deepcopy(self.events)
        next(e for e in events if e['kind'] == 's274_life' and ',4,' in e['value'])['kind'] = 'removed'
        with self.assertRaisesRegex(ValueError, 'controls missing'):
            diag.analyze(events)

    def test_generation_change_rejects(self):
        events = copy.deepcopy(self.events)
        e = next(e for e in events if e['kind'] == 's274_state' and e['value'].startswith('draw_after,'))
        e['value'] = e['value'].replace(',-16381,1,', ',-16381,2,')
        with self.assertRaisesRegex(ValueError, 'unbound actual'):
            diag.analyze(events)

    def test_admission_missing(self):
        with self.assertRaisesRegex(ValueError, 'admission missing'):
            diag.analyze(self.changed('s274_admission', 'true', 'false'))

    def test_encoding_boundary_missing(self):
        with self.assertRaisesRegex(ValueError, 'boundaries incomplete'):
            diag.analyze(self.changed('s274_memory', 'encoding_after'))

    def test_zero_encoding_work_rejects(self):
        with self.assertRaisesRegex(ValueError, 'encoded work'):
            diag.analyze(self.changed('s274_encoded_size', '', '0'))

    def test_no_pixels_allowed(self):
        events = copy.deepcopy(self.events)
        events[-1]['kind'] = 'bitmap_row'
        with self.assertRaisesRegex(ValueError, 'pixel export'):
            diag.analyze(events)

    def test_no_cross_run_join(self):
        events = copy.deepcopy(self.events)
        events[-1]['run'] = 's262-transplant'
        with self.assertRaisesRegex(ValueError, 'mixed capture'):
            diag.analyze(events)

    def test_missing_actual_entry_does_not_prove_bridge(self):
        events = copy.deepcopy(self.events)
        for e in events:
            if e['kind'] == 's274_entry' and '.个,' in e['value'] and e['tick'] >= 0:
                e['kind'] = 'missing_actual_entry'
        result = diag.analyze(events)
        self.assertFalse(result['bounded_encoded_lifetime_observed'])
        self.assertFalse(result['thin_state_admission_proved'])

    def test_missing_next_callback_does_not_prove_bridge(self):
        events = copy.deepcopy(self.events)
        for e in events:
            if e['kind'] == 's258_countdown' and e['value'].startswith('fire_before,'):
                e['kind'] = 'missing_callback'
        with self.assertRaisesRegex(ValueError, 'callback pairs incomplete'):
            diag.analyze(events)


if __name__ == '__main__':
    unittest.main()
