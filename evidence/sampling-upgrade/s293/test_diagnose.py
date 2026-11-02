"""Retain source-derived closure boundaries and independent host checks and honest unproved gates."""
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
        self.assertIs(self.report['independent_pair_proved'], True)
        self.assertIs(self.report['locked_s284_independent_pair_proved'], False)

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
        self.assertTrue(self.report['runs']['normal']['host_log_equality']['equal'])
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



    def host_fixture(self):
        import gzip, json
        base = diagnose.HERE / 'normal'
        return (gzip.decompress((base / 'host-log.txt.gz').read_bytes()),
                gzip.decompress((base / 'native-capture.log.gz').read_bytes()),
                json.loads((base / 'native-build.json').read_text()),
                json.loads((base / 'host-log-equality.json').read_text()))

    def test_host_bytes_recomputed(self):
        self.assertTrue(diagnose.check_host(*self.host_fixture())['equal'])
        self.assertTrue(self.report['each_host_archived_and_checked_before_next_launch'])

    def test_host_duplicate_not_deduplicated(self):
        host, trace, meta, check = self.host_fixture()
        with self.assertRaisesRegex(ValueError, 'S293_HOST_LOG_MISMATCH'):
            diagnose.check_host(host + trace.splitlines()[0] + b'\n', trace, meta, check)

    def test_host_reordering_not_sorted_away(self):
        host, trace, meta, check = self.host_fixture()
        rows = trace.splitlines()
        rows[0], rows[1] = rows[1], rows[0]
        with self.assertRaisesRegex(ValueError, 'S293_HOST_LOG_MISMATCH'):
            diagnose.check_host(b'\n'.join(rows) + b'\n', trace, meta, check)

    def test_true_boolean_cannot_replace_host_bytes(self):
        host, trace, meta, check = self.host_fixture()
        with self.assertRaisesRegex(ValueError, 'S293_HOST_LOG_MISMATCH'):
            diagnose.check_host(b'', trace, meta, check)

    def test_full_host_hash_includes_non_run_lines(self):
        host, trace, meta, check = self.host_fixture()
        with self.assertRaisesRegex(ValueError, 'S293_HOST_RECORD_MISMATCH'):
            diagnose.check_host(b'extra diagnostic\n' + host, trace, meta, check)

    def test_late_host_check_rejected(self):
        import copy, json
        records = json.loads((diagnose.HERE / 'execution.json').read_text())
        runs = copy.deepcopy(self.report['runs'])
        records[0]['host_checked_at'] = records[1]['archiving_finished_at']
        runs['normal']['host_log_equality']['checked_at'] = records[0]['host_checked_at']
        with self.assertRaisesRegex(ValueError, 'S293_ARCHIVE_ORDER_UNPROVED'):
            diagnose.check_sequence(records, runs)

    def test_duplicate_pair_identity_rejected(self):
        import copy, json
        records = json.loads((diagnose.HERE / 'execution.json').read_text())
        runs = copy.deepcopy(self.report['runs'])
        runs['held']['run_id'] = runs['normal']['run_id']
        with self.assertRaisesRegex(ValueError, 'S293_PAIR_IDENTITY_INVALID'):
            diagnose.check_sequence(records, runs)


if __name__ == '__main__':
    unittest.main()
