import json
from pathlib import Path
import tempfile
import unittest

from tools.probes import yulong_display_completion as observer

ROOT = Path(__file__).resolve().parents[2]


class DisplayCompletionProbeTests(unittest.TestCase):
    def test_only_terminal_control_statements_are_added(self):
        source = (ROOT / 'tools/probes/as2/ai_reference/bootstrap.as').read_text()
        result = observer.instrument(source)
        self.assertEqual(result.replace(observer.FLAG, '').replace(observer.GUARD, '').replace(observer.ARM, ''), source)
        self.assertLess(result.index(observer.GUARD), result.index('   aiDisplay++;'))
        self.assertLess(result.index(observer.DONE), result.index(observer.ARM))
        self.assertLess(result.index(observer.ARM), result.index('fscommand("quit")'))
        # The arm does not mute callbacks belonging to the terminal root period.
        self.assertNotIn('aiEvent =', observer.ARM)

    def test_changed_or_ambiguous_boundaries_reject(self):
        source = (ROOT / 'tools/probes/as2/ai_reference/bootstrap.as').read_text()
        for bad in (source.replace(observer.DONE, ''), source + observer.DONE,
                    source.replace('   aiDisplay++;', '   aiDisplay += 2;')):
            with self.subTest(source=bad[:30]), self.assertRaises(ValueError):
                observer.instrument(bad)

    def test_control_moves_only_the_terminal_quit(self):
        from tools.probes.build_yulong_display_hold import defer_quit
        source = observer.instrument((ROOT / 'tools/probes/as2/ai_reference/bootstrap.as').read_text())
        result = defer_quit(source)
        self.assertEqual(source[:source.index(observer.FLAG)], result[:result.index(observer.FLAG)])
        self.assertEqual(source.count('fscommand("quit")'), result.count('fscommand("quit")'))
        restored = result.replace('      _root.aiEvent = function() {};\n      fscommand("quit");',
                                  '      _root.aiEvent = function() {};').replace(
            observer.DONE + observer.ARM, observer.DONE + observer.ARM + '\n      fscommand("quit");')
        self.assertEqual(restored, source)
        with self.assertRaises(ValueError):
            defer_quit(result)

    def test_only_unchanged_case(self):
        case = ROOT / 'evidence/sampling-upgrade/s240/yulong__attack__neutral__ground__near.json'
        observer.validate_case(case)
        data = json.loads(case.read_text()); data['frames'] = 61
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'case.json'; path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                observer.validate_case(path)
        with self.assertRaises(ValueError):
            observer.validate_case(None)


class DisplayCompletionEvidenceTests(unittest.TestCase):
    def setUp(self):
        import gzip
        base = ROOT / 'evidence/sampling-upgrade/s248/first-capture'
        self.lines = gzip.open(base / 'native-capture.log.gz', 'rt').read().splitlines()
        self.metadata = json.loads((base / 'native-build.json').read_text())
        self.case = self.metadata['move_case']

    def validate_lines(self, lines):
        from tools.sampling_native import validate_capture
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'native.log'; path.write_text('\n'.join(lines) + '\n')
            validate_capture(self.case, self.metadata, path)

    def test_complete_final_display_sample_is_required(self):
        from tools.sampling_display import collect
        samples = collect(self.lines, self.metadata['run_id'], 60)
        self.assertEqual([s['tick'] for s in samples], list(range(61)))
        changed = [line for line in self.lines if not ('|60|display_end|' in line)]
        with self.assertRaises(ValueError):
            collect(changed, self.metadata['run_id'], 60)
        with self.assertRaises(ValueError):
            self.validate_lines(changed)

    def test_duplicate_done_remains_rejected(self):
        row = next(line.split('|', 7) for line in self.lines if '|done|' in line)
        row[2] = str(len(self.lines) + 1)
        with self.assertRaisesRegex(ValueError, 'completion'):
            self.validate_lines(self.lines + ['|'.join(row)])

    def test_post_boundary_event_remains_rejected(self):
        row = self.lines[-1].split('|', 7)
        row[2] = str(len(self.lines) + 1); row[4] = str(int(row[4]) + 1); row[5] = '61'
        with self.assertRaisesRegex(ValueError, 'beyond completion boundary'):
            self.validate_lines(self.lines + ['|'.join(row)])

    def test_held_exit_exercises_guard_and_retains_terminal_callbacks(self):
        import gzip
        rows = [line.split('|', 7) for line in gzip.open(
            ROOT / 'evidence/sampling-upgrade/s248/native-capture.log.gz', 'rt').read().splitlines()]
        dones = [i for i, row in enumerate(rows) if row[6] == 'done']
        self.assertEqual(len(dones), 1)
        index = dones[0]
        self.assertEqual(rows[-1][6], 'capture_window_closed')
        self.assertGreater(len(rows[index + 1:-1]), 0)
        self.assertTrue(all(row[4:6] == rows[index][4:6] for row in rows[index + 1:]))
        self.assertEqual(len([row for row in rows if row[6] == 'display_begin']), 61)

    def test_retained_s240_trace_still_rejects(self):
        import gzip
        from tools.sampling_native import validate_capture
        base = ROOT / 'evidence/sampling-upgrade/s240'
        raw = gzip.open(base / 'native-capture.log.gz', 'rt').read()
        metadata = json.loads((base / 'native-build.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'native.log'; path.write_text(raw)
            with self.assertRaisesRegex(ValueError, 'beyond completion boundary'):
                validate_capture(metadata['move_case'], metadata, path)


if __name__ == '__main__':
    unittest.main()
