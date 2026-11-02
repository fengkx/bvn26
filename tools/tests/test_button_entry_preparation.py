"""Source preservation and fail-closed boundaries of the unexecuted s276 UI case."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s276'


def load(name):
    spec = importlib.util.spec_from_file_location('s276_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ButtonEntryPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepare = load('prepare_probe')
        cls.scripts = {s['path']: s['source'] for s in json.loads((ROOT / 'scripts/main.json').read_text())['scripts']}
        cls.report = load('diagnose').diagnose()

    def test_entries_preserve_exact_original_source(self):
        patches = self.prepare.patches(self.scripts)
        for event, label in [('keyPress Enter', 'enter_entry'), ('release', 'release_entry')]:
            path = self.prepare.BUTTON.format(event)
            marker = f'   _root.s276Observe("{label}", this);\r\n'
            self.assertEqual(patches[path].count(marker), 1)
            self.assertEqual(patches[path].replace(marker, ''), self.scripts[path])
            self.assertLess(patches[path].index(marker), patches[path].index('gotoAndStop(1)'))

    def test_changed_handler_rejected(self):
        scripts = dict(self.scripts)
        path = self.prepare.BUTTON.format('release')
        scripts[path] = scripts[path].replace('gotoAndStop(1)', 'gotoAndStop(2)')
        with self.assertRaisesRegex(ValueError, 'changed Button2009'):
            self.prepare.patches(scripts)

    def test_ambiguous_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            self.prepare.insert_once('xx', 'x', 'marker')

    def test_unknown_observations_are_not_zero_execution(self):
        for key in ('frame10_observed', 'enter_dispatch_observed', 'release_dispatch_observed',
                    'handler_entries_observed', 'no_dispatch_controls_observed',
                    'listener_order_observed', 'handler_return_observed'):
            self.assertIsNone(self.report[key])

    def test_preparation_never_admits_coverage(self):
        for key in ('production_admitted', 'native_parity_proven', 'thin_coverage_cut_proved',
                    'ui_case_executed', 'candidate_compiled', 'candidate_opcode_preservation_checked'):
            self.assertFalse(self.report[key])
        self.assertEqual(self.report['product_obligations_closed'], 0)
        self.assertEqual(self.report['locked_replay']['strict_full_as_exit'], 1)
        self.assertEqual(len(self.report['family_obligations']), 2)

    def test_frame_stop_mutation_rejected(self):
        scripts = dict(self.scripts)
        scripts['DefineSprite_2010/frame_10/DoAction.as'] = 'play();\r\n'
        with self.assertRaisesRegex(ValueError, 'changed menu stop'):
            self.prepare.patches(scripts)


if __name__ == '__main__':
    unittest.main()
