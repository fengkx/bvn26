"""Keep source ordering, independent reads and runtime controls distinct."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s277'


class LoaderReadTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('s277_diagnose', HERE / 'diagnose.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.report = cls.module.diagnose()
        cls.source = next(s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts']
                          if s['path'] == 'DefineSprite_1900/frame_1/DoAction.as')

    def test_full_normal_trace_recomputed(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual(self.report['historical_normal']['events'], 5503)

    def test_source_order_is_not_callback_schedule(self):
        order = self.report['source_loader_order']
        self.assertTrue(order['completion_calls_next_step_inline'])
        self.assertFalse(order['on_load_init_listener_present'])
        self.assertIsNone(order['actual_callback_order'])

    def test_changed_order_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'changed source load order'):
            self.module.loader_order(self.source.replace('loadman("p1");', 'loadman("p2");'))

    def test_changed_completion_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'changed shared loader/callback'):
            self.module.loader_order(self.source.replace('loadStep++;', 'loadStep += 2;'))

    def test_static_imports_do_not_fill_live_observations(self):
        self.assertIn('_read', self.report['native_read_import_candidates'])
        for key in ('independent_read_request_callback_observation',
                    'actual_wrong_resource_load_control', 'bounded_target_lifetime'):
            self.assertIsNone(self.report[key])
        for key in ('loader_attestation_proved', 'production_admitted', 'native_parity_proven'):
            self.assertFalse(self.report[key])

    def test_requirement_remains_red(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-m', 'evidence.sampling-upgrade.s277.diagnose',
                                     '--output', str(Path(directory) / 'result.json'),
                                     '--require-loader-attestation'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('S277_LOADER_ATTESTATION_UNPROVED', result.stdout)


if __name__ == '__main__':
    unittest.main()
