"""Retain source-derived closure boundaries and honest unproved gates."""
from pathlib import Path
import tempfile
import unittest

import diagnose
from tools.sampling_native import validate_capture


class CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = diagnose.diagnose()

    def test_admission_stays_closed(self):
        self.assertIs(self.report['production_admitted'], False)
        self.assertIs(self.report['native_parity_proven'], False)
        self.assertIs(self.report['independent_pair_proved'], False)

    def test_historical_full_suffix_still_rejects(self):
        self.assertEqual(self.report['historical_rejection'], 'native evidence: events beyond completion boundary')

    def test_final_requested_sample_preserved(self):
        for run in self.report['runs'].values():
            self.assertEqual(run['samples'], 61)
            self.assertEqual(run['done'][5:7], ['60', 'done'])
            self.assertTrue(run['qualification']['source_preserving_build_qualified'])

    def test_held_closes_before_next_increment(self):
        run = self.report['runs']['held']
        self.assertEqual(run['terminal_suffix'][-1][6:8], ['capture_window_closed','before-next-root-increment'])
        for row in run['terminal_suffix']:
            self.assertEqual(row[4:6], run['done'][4:6])
        self.assertTrue(all(row[6]=='key_read' for row in run['terminal_suffix'][:-1]))

    def test_normal_absence_is_not_completeness(self):
        self.assertEqual(self.report['runs']['normal']['terminal_suffix'], [])
        self.assertIs(self.report['terminal_callback_completeness_proved'], False)
        self.assertIsNone(self.report['runs']['normal']['host_log_equality']['equal'])
        self.assertTrue(self.report['runs']['held']['host_log_equality']['equal'])

    def test_requested_state_and_inputs_preserved(self):
        for run in self.report['runs'].values():
            for kind in ('state','helper_state','helper_clip_state','helper_lifecycle','input_next_display'):
                self.assertTrue(run['comparison_to_s228_ticks_0_60'][kind]['tick_payload_equal'])
            self.assertTrue(run['key_reads_before_terminal_equal'])

    def test_random_difference_remains_visible(self):
        for run in self.report['runs'].values():
            self.assertFalse(run['comparison_to_s228_ticks_0_60']['random']['tick_payload_equal'])

    def test_full_as_stays_negative(self):
        for run in self.report['runs'].values():
            self.assertEqual(run['full_as_gate']['exit_code'], 1)
            self.assertIn('statement/call ownership unproven',run['full_as_gate']['error'])

    def test_unrelated_root_edit_fails_source_erasure(self):
        import json, tarfile
        from qualify import qualify
        base = diagnose.HERE/'held'
        receipt = json.loads((base/'receipt.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            build = Path(directory)
            with tarfile.open(base/'native-build.tar.gz') as archive:
                for member in archive.getmembers():
                    if member.isfile():
                        target = build/member.name
                        self.assertTrue(target.resolve().is_relative_to(build.resolve()))
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())
            patch = build/'patches/main/frame_10/DoAction.as'
            patch.write_text(patch.read_text().replace('aiDisplay++;','aiDisplay += 2;'))
            with self.assertRaisesRegex(ValueError,'erase to the archived root'):
                qualify(build,True,receipt['build'])

    def test_later_root_event_rejected(self):
        import gzip, json
        base = diagnose.HERE/'held'
        text = gzip.decompress((base/'native-capture.log.gz').read_bytes()).decode()
        meta = json.loads((base/'native-build.json').read_text())
        row = text.splitlines()[-1].split('|',7)
        row[2] = str(int(row[2])+1)
        row[4] = str(int(row[4])+1)
        row[5] = '61'
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory)/'negative.log'
            trace.write_text(text+'|'.join(row)+'\n')
            with self.assertRaisesRegex(ValueError,'events beyond completion boundary'):
                validate_capture(json.loads(diagnose.CASE.read_text()),meta,trace)


if __name__ == '__main__':
    unittest.main()
