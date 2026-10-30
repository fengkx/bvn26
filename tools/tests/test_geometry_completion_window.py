"""Retain the exact s259 geometry completion control and strict rejections."""
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools.probes.yulong_display_completion import instrument
from tools.sampling_geometry import collect
from tools.sampling_native import validate_capture

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s259'


def load(name):
    spec = importlib.util.spec_from_file_location('s259_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GeometryCompletionWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = load('diagnose').diagnose()
        cls.metadata = json.loads((HERE / 'held/native-build.json').read_text())
        cls.lines = gzip.decompress((HERE / 'held/native-capture.log.gz').read_bytes()).decode().splitlines()
        cls.sources = set()
        for path in cls.metadata['sources_sha256']:
            if path.startswith('scripts/') and path.endswith('.json'):
                bundle = json.loads((ROOT / path).read_text())
                cls.sources.update(bundle['game_file'] + '#' + s['path'] for s in bundle['scripts'])

    def validate(self, lines):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / 'native.log'
            trace.write_text('\n'.join(lines) + '\n')
            validate_capture(self.metadata['move_case'], self.metadata, trace)

    def test_report_recomputes(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertFalse(self.report['production_admitted'])
        self.assertFalse(self.report['native_parity_proven'])
        self.assertIn('events beyond completion boundary', self.report['historical_rejection'])

    def test_native_held_control_retains_terminal_period(self):
        r = self.report['runs']['held']
        self.assertEqual(r['event_count'], 5416)
        self.assertEqual([x[6] for x in r['terminal_suffix']], ['key_read'] * 34 + ['capture_window_closed'])
        self.assertTrue(all(x[4:6] == r['done_event'][4:6] for x in r['terminal_suffix']))
        self.assertEqual(r['terminal_geometry'][-1][6:], ['geometry_end', '4,4'])
        self.assertEqual((r['samples'], r['boxes']), (61, 240))
        self.assertEqual(r['missing_receivers'], [])
        self.assertTrue(r['comparison_to_s232_ticks_0_60']['key_read']['tick_payload_equal'])
        self.validate(self.lines)

    def test_normal_control_does_not_claim_guard_execution(self):
        r = self.report['runs']['normal']
        self.assertEqual(r['terminal_suffix'], [])
        self.assertTrue(r['key_reads_before_terminal_equal'])
        self.assertEqual(r['comparison_to_s232_ticks_0_60']['state']['fresh_count'], 122)
        self.assertTrue(r['comparison_to_s232_ticks_0_60']['state']['tick_payload_equal'])

    def test_missing_final_geometry_end_rejects_even_with_valid_state_receipt(self):
        lines = [line for line in self.lines if '|60|geometry_end|' not in line]
        # Geometry completeness remains the dimension gate's responsibility.
        with self.assertRaises(ValueError):
            collect(lines, self.metadata['run_id'], 60, self.sources)

    def test_bad_terminal_geometry_count_rejects(self):
        lines = [line.replace('|60|geometry_end|4,4', '|60|geometry_end|3,4') for line in self.lines]
        with self.assertRaisesRegex(ValueError, 'counts'):
            collect(lines, self.metadata['run_id'], 60, self.sources)

    def test_missing_terminal_callback_rejects_sequence_gap(self):
        with self.assertRaises(ValueError):
            self.validate(self.lines[:-2] + self.lines[-1:])

    def test_later_root_still_rejects(self):
        row = self.lines[-1].split('|', 7)
        row[2] = str(len(self.lines) + 1)
        row[4] = str(int(row[4]) + 1)
        row[5] = '61'
        with self.assertRaisesRegex(ValueError, 'beyond completion boundary'):
            self.validate(self.lines + ['|'.join(row)])

    def test_window_and_held_control_only_change_observer_boundaries(self):
        original = 'onEnterFrame = function()\n{\n   aiDisplay++;\n   _root.aiGeometrySample();\n      aiEvent("done", "");\n      fscommand("quit");\n};'
        patched = instrument(original)
        self.assertLess(patched.index('capture_window_closed'), patched.index('aiDisplay++;'))
        self.assertLess(patched.index('aiGeometrySample'), patched.index('aiEvent("done"'))
        held = load('build_probe').defer_quit(patched)
        self.assertEqual(held.count('fscommand("quit")'), 1)
        self.assertLess(held.index('fscommand("quit")'), held.index('aiDisplay++;'))
        with self.assertRaises(ValueError):
            load('build_probe').defer_quit(original)
