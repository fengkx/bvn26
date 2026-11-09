"""Retained live provenance and fail-closed continuation regressions."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from analyze import HERE, analyze


class ReceiptTests(unittest.TestCase):
    def test_full_prefix_stays_refused(self):
        report = analyze(HERE / 'run-01')
        for flag in ['production_admitted', 'native_parity_proven', 'oracle_accepted', 'certified_global_tick', 'os_input_join_proven']:
            self.assertIs(report[flag], False)
        self.assertEqual(report['structural_refusal'], 'Incomplete actor state at clock boundary')
        self.assertGreater(len(report['incomplete_clock_boundaries']), 0)
        self.assertTrue(report['fresh_exclusive_tag_selection'])
        self.assertTrue(report['all_copy_hashes_and_tags_match'])

    def test_actual_direct_before_without_after_stays_refused(self):
        report = analyze(HERE / 'run-01')
        self.assertEqual(report['side_counts'], {'before': 1})
        self.assertEqual(report['counts'].get('continuation-prep'), 1)
        self.assertEqual(report['counts'].get('continuation-breadcrumb', 0), 0)
        self.assertEqual(report['counts'].get('consumer-goto-after', 0), 0)
        outcome, = report['direct_analysis']['outcomes']
        self.assertEqual(outcome['classification'], 'before-without-after')
        self.assertEqual(outcome['cause'], 'unproved')
        self.assertIs(outcome['source_continuation_observed'], False)
        self.assertEqual(report['consumer_analysis']['validated_predicates'], {'false': 196})
        refused = [x for x in report['consumer_analysis']['intervals'] if 'refusal' in x]
        self.assertEqual(len(refused), 1)
        self.assertEqual(refused[0]['key_join_status'], 'not-joined')

    def test_raw_selection_tampering_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name in ['session.json', 'flashlog.prelaunch.log', 'flashlog.input-baseline.log', 'flashlog.after.log', 'tagged.log', 'combined.log']:
                shutil.copyfile(HERE / 'run-01' / name, directory / name)
            raw = (directory / 'tagged.log').read_bytes()
            (directory / 'tagged.log').write_bytes(raw.split(b'\n', 1)[1])
            with self.assertRaisesRegex(ValueError, 'Raw/tag selection'):
                analyze(directory)

    def test_combined_reordering_and_foreign_side_refused(self):
        for mode in ['reorder', 'foreign']:
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                for name in ['session.json', 'flashlog.prelaunch.log', 'flashlog.input-baseline.log', 'flashlog.after.log', 'tagged.log', 'combined.log']:
                    shutil.copyfile(HERE / 'run-01' / name, directory / name)
                if mode == 'reorder':
                    raw = (directory / 'combined.log').read_bytes()
                    (directory / 'combined.log').write_bytes(b'\n'.join(reversed(raw.splitlines()))+b'\n')
                    message = 'Combined raw order'
                else:
                    for name in ['combined.log', 'flashlog.after.log']:
                        with (directory / name).open('ab') as target:
                            target.write(b'M002SIDE|foreign,helper,1,doAllAction|before\n')
                    message = 'Foreign side tag'
                with self.assertRaisesRegex(ValueError, message):
                    analyze(directory)

    def test_build_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            session = json.loads((HERE / 'run-01/session.json').read_text())
            session['observer_build']['run_id'] = 'foreign'
            (directory / 'session.json').write_text(json.dumps(session))
            with self.assertRaisesRegex(ValueError, 'Build/session'):
                analyze(directory)

    def test_cleanup_and_pid_binding_refused(self):
        for mode in ['cleanup', 'pid']:
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                for name in ['session.json', 'flashlog.prelaunch.log', 'flashlog.input-baseline.log', 'flashlog.after.log', 'tagged.log', 'combined.log']:
                    shutil.copyfile(HERE / 'run-01' / name, directory / name)
                session = json.loads((directory / 'session.json').read_text())
                if mode == 'cleanup':
                    session['remaining_movie_pids'] = [session['movie_pid']]
                else:
                    session['input_operations'][0]['pid'] += 1
                (directory / 'session.json').write_text(json.dumps(session))
                with self.assertRaises(ValueError):
                    analyze(directory)


if __name__ == '__main__':
    unittest.main()
