"""Protect byte provenance and reject unsupported entry-clock claims."""
import importlib.util
import json
from pathlib import Path
import tarfile
import unittest
import zlib

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('s292', HERE / 'diagnose.py')
s292 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s292)


def mutate(raw, offset, value):
    data = bytearray(raw if raw[:3] == b'FWS' else raw[:8] + zlib.decompress(raw[8:]))
    data[:3] = b'FWS'
    data[offset] = value
    return bytes(data)


class EntryQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (s292.ROOT / 'game/main.swf').read_bytes()
        with tarfile.open(HERE.parent / 's274/native-build.tar.gz') as archive:
            cls.archived = archive.extractfile('game/main.swf').read()
            cls.source = archive.extractfile('s274-patches/frame_1/DoAction.as').read().decode()
        cls.lifetime = json.loads((HERE.parent / 's274/diagnosis.json').read_text())

    def test_replay_and_fail_closed(self):
        report = s292.diagnose()
        self.assertEqual(report['historical']['callback_count'], 63)
        self.assertEqual(report['historical']['natural_encoding_entry_joins'], 4)
        self.assertEqual(report['historical']['uninstrumented_target_windows'], 45)
        self.assertEqual(len(report['unobserved_frame1_windows']), 14)
        for row in report['unobserved_frame1_windows']:
            self.assertIsNone(row['independent_target_entry_observed'])
        for key in ('observer_qualified', 'independent_child_clock_proved',
                    'production_admitted', 'native_parity_proven'):
            self.assertIs(report[key], False)
        self.assertEqual(report['new_captures'], 0)

    def test_byte_preservation_is_not_execution_equivalence(self):
        report = s292.byte_audit(self.original, self.archived)
        self.assertTrue(report['non_action_timeline_bytes_equal'])
        self.assertTrue(report['terminal_stop_retained'])
        self.assertFalse(report['unchanged_action_execution_proved'])
        self.assertEqual(report['empty_frames_without_observer'], list(range(2, 11)))

    def test_changed_original_stop_rejected(self):
        tag = next(r for r in s292.digit_tags(self.original) if r['code'] == 12)
        with self.assertRaisesRegex(ValueError, 'original Stop'):
            s292.byte_audit(mutate(self.original, tag['payload_offset'], 6), self.archived)

    def test_changed_archived_stop_rejected(self):
        tag = next(r for r in s292.digit_tags(self.archived) if r['code'] == 12)
        offset = tag['payload_offset'] + len(bytes.fromhex(tag['payload_hex'])) - 2
        with self.assertRaisesRegex(ValueError, 'terminal Stop'):
            s292.byte_audit(self.original, mutate(self.archived, offset, 6))

    def test_changed_placement_rejected(self):
        tag = next(r for r in s292.digit_tags(self.archived) if r['code'] == 26 and r['frame'] == 2)
        with self.assertRaisesRegex(ValueError, 'non-action'):
            s292.byte_audit(self.original, mutate(self.archived, tag['payload_offset'], 0))

    def test_bad_swf_length_rejected(self):
        with self.assertRaisesRegex(ValueError, 'length'):
            s292.digit_tags(mutate(self.original, 4, 0))

    def test_truncated_action_rejected(self):
        with self.assertRaisesRegex(ValueError, 'truncated action'):
            s292.actions('96050000')

    def test_trailing_action_rejected(self):
        with self.assertRaisesRegex(ValueError, 'trailing action'):
            s292.actions('070007')

    def test_missing_action_end_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing action end'):
            s292.actions('07')

    def test_controls_are_not_independent_all_frame_proof(self):
        report = s292.control_audit(self.source, self.lifetime)
        self.assertTrue(all(v is None for v in report['independent_controls'].values()))
        self.assertEqual(len(report['historical_retained_entries']), 2)
        self.assertFalse(report['actor_equality_is_entry_order_control'])

    def test_changed_control_goto_rejected(self):
        with self.assertRaisesRegex(ValueError, 'control changed'):
            s292.control_audit(self.source.replace('gotoAndStop(2);', 'gotoAndStop(3);'), self.lifetime)

    def test_missing_replacement_rejected(self):
        with self.assertRaisesRegex(ValueError, 'replacement changed'):
            s292.control_audit(self.source.replace('removeMovieClip();', 'stop();'), self.lifetime)


if __name__ == '__main__':
    unittest.main()
