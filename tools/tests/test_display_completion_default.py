"""Retained non-Yulong proof of the default display observation window."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest

from tools.sampling_native import validate_capture
from tools.sampling_display import collect

ROOT = Path(__file__).resolve().parents[2]


class DefaultDisplayCompletionTests(unittest.TestCase):
    def setUp(self):
        base = ROOT / 'evidence/sampling-upgrade/s249'
        self.metadata = json.loads((base / 'native-build.json').read_text())
        self.lines = gzip.open(base / 'native-capture.log.gz', 'rt').read().splitlines()

    def validate_lines(self, lines):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'native.log'
            path.write_text('\n'.join(lines) + '\n')
            validate_capture(self.metadata['move_case'], self.metadata, path)

    def test_default_non_yulong_capture_keeps_terminal_period(self):
        self.assertFalse(self.metadata['yulong_display_completion'])
        self.assertTrue(self.metadata['display_completion_window'])
        self.assertEqual(self.metadata['move_case']['id'], 'yijiao__attack__neutral__ground__near')
        self.validate_lines(self.lines)
        rows = [line.split('|', 7) for line in self.lines]
        done = [i for i, row in enumerate(rows) if row[6] == 'done']
        self.assertEqual(len(done), 1)
        self.assertEqual(rows[-1][6], 'capture_window_closed')
        self.assertGreater(len(rows[done[0] + 1:-1]), 0)
        self.assertTrue(all(row[4:6] == rows[done[0]][4:6] for row in rows[done[0] + 1:]))
        self.assertEqual(len(collect(self.lines, self.metadata['run_id'], 60)), 61)

    def test_final_display_sample_cannot_be_removed(self):
        changed = [line for line in self.lines if '|60|display_end|' not in line]
        with self.assertRaises(ValueError):
            collect(changed, self.metadata['run_id'], 60)
        with self.assertRaises(ValueError):
            self.validate_lines(changed)

    def test_later_root_boundary_still_rejects(self):
        row = self.lines[-1].split('|', 7)
        row[2] = str(len(self.lines) + 1)
        row[4] = str(int(row[4]) + 1)
        row[5] = '61'
        with self.assertRaisesRegex(ValueError, 'beyond completion boundary'):
            self.validate_lines(self.lines + ['|'.join(row)])

    def test_old_s233_capture_still_rejects(self):
        base = ROOT / 'evidence/sampling-upgrade/s233'
        self.metadata = json.loads((base / 'native-build.json').read_text())
        lines = gzip.open(base / 'native-capture.log.gz', 'rt').read().splitlines()
        with self.assertRaisesRegex(ValueError, 'beyond completion boundary'):
            self.validate_lines(lines)
