"""Bound s269 to its retained callsite case and preserve strict negative gates."""
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from tools.probes.yulong_display_completion import instrument
from tools.sampling_callsite import collect_calls
from tools.sampling_doaction import collect, check_inventory
from tools.sampling_native import validate_capture

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s269'


def load(name):
    spec = importlib.util.spec_from_file_location('s269_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CallsiteCompletionWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = load('diagnose').diagnose()
        cls.meta = json.loads((HERE / 'held/native-build.json').read_text())
        cls.lines = gzip.decompress((HERE / 'held/native-capture.log.gz').read_bytes()).decode().splitlines()

    def validate(self, lines):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / 'native.log'
            trace.write_text('\n'.join(lines) + '\n')
            validate_capture(self.meta['move_case'], self.meta, trace)

    def test_recompute_and_old_rejection(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        historical = load('classify').diagnose()
        self.assertEqual(historical, json.loads((HERE / 'historical-classification.json').read_text()))
        self.assertEqual(len(historical['terminal_period_callbacks']), 51)
        self.assertEqual(len(historical['later_root_events']), 11)
        self.assertEqual(historical['native_gate']['exit_code'], 1)
        self.assertEqual(len(historical['terminal_invocations']), 1)
        self.assertFalse(self.report['production_admitted'])
        self.assertFalse(self.report['native_parity_proven'])

    def test_held_preserves_call_pair_before_closure(self):
        r = self.report['runs']['held']
        self.assertEqual(r['samples'], 61)
        self.assertEqual(r['terminal_suffix'][-1][6], 'capture_window_closed')
        phases = [x[7].split(',')[1] for x in r['terminal_suffix'] if x[6] == 'callsite']
        self.assertEqual(phases, ['predicate_before', 'true', 'call_before', 'call_after', 'end'])
        self.assertTrue(all(x[4:6] == r['done_event'][4:6] for x in r['terminal_suffix']))
        self.validate(self.lines)

    def test_measured_actor_and_input_controls(self):
        for r in self.report['runs'].values():
            self.assertEqual(r['samples'], 61)
            for kind in ('state', 'input_next_display', 'helper_state', 'helper_clip_state', 'helper_lifecycle'):
                self.assertTrue(r['comparison_to_s223_ticks_0_60'][kind]['tick_payload_equal'])
            self.assertEqual(r['comparison_to_s223_ticks_0_60']['state']['fresh_count'], 122)

    def test_missing_terminal_callback_rejects(self):
        with self.assertRaises(ValueError):
            self.validate(self.lines[:-2] + self.lines[-1:])

    def test_later_root_rejects(self):
        row = self.lines[-1].split('|', 7)
        row[2], row[4], row[5] = str(len(self.lines) + 1), str(int(row[4]) + 1), '61'
        with self.assertRaisesRegex(ValueError, 'beyond completion boundary'):
            self.validate(self.lines + ['|'.join(row)])

    def test_missing_call_after_is_not_completion(self):
        lines = [x for x in self.lines if not ('|60|callsite|' in x and ',call_after,' in x)]
        with self.assertRaisesRegex(ValueError, 'missing/duplicate/out-of-order'):
            collect_calls(lines, self.meta['callsite_specification'], retain_incomplete=True)

    def test_missing_final_sample_rejects(self):
        lines = [x for x in self.lines if '|60|doaction_sample|' not in x]
        with self.assertRaises(ValueError):
            collect(lines, self.meta['run_id'], 60, check_inventory(self.meta))

    def test_existing_incomplete_invocation_stays_rejected(self):
        for mode in ('normal', 'held'):
            meta = json.loads((HERE / mode / 'native-build.json').read_text())
            lines = gzip.decompress((HERE / mode / 'native-capture.log.gz').read_bytes()).decode().splitlines()
            with self.assertRaisesRegex(ValueError, 'incomplete/reentrant'):
                collect_calls(lines, meta['callsite_specification'])

    def test_only_explicit_wrapper_changes_quit(self):
        original = 'onEnterFrame = function()\n{\n   aiDisplay++;\n   aiEvent("doaction_sample", "root-observer");\n      aiEvent("done", "");\n      fscommand("quit");\n};'
        patched = instrument(original)
        self.assertLess(patched.index('capture_window_closed'), patched.index('aiDisplay++;'))
        held = load('build_probe').defer_quit(patched)
        self.assertEqual(held.count('fscommand("quit")'), 1)
        self.assertLess(held.index('fscommand("quit")'), held.index('aiDisplay++;'))
        with self.assertRaises(ValueError):
            load('build_probe').defer_quit(original)
