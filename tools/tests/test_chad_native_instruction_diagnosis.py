"""Keep native startup, static instructions and executed AVM1 proof distinct."""
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parents[2] / 'evidence/sampling-upgrade/s278'
spec = importlib.util.spec_from_file_location('s278_diagnose', HERE / 'diagnose.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ChadNativeInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = module.diagnose()

    def test_reproduce_complete_locked_evidence(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual(self.report['historical']['events'], 9493)
        self.assertEqual(self.report['historical']['actor_comparison']['rows'], 122)

    def test_entry_stop_is_not_avm1_observation(self):
        self.assertTrue(self.report['native_cpu_entry_stop_observed'])
        for key in ('production_admitted', 'native_parity_proven',
                    'native_instruction_activation_facility_qualified', 'exact_continuation_proved'):
            self.assertFalse(self.report[key])
        for key in ('native_avm1_pc', 'operand_stack', 'defining_activation', 'executed_retained_control'):
            self.assertIsNone(self.report[key])

    def test_retained_control_does_not_create_chad_after_event(self):
        old = self.report['historical']
        self.assertEqual([r['post'] for r in old['controls']], ['1', '0'])
        self.assertEqual([r['post'] for r in old['dynamic_controls']], ['1', '1'])
        self.assertEqual(old['missing_boundaries'], ['goto_after', 'callee_exit', 'caller_after'])
        self.assertEqual(old['full_as'], {'unvisited': 594, 'uninstrumented': 415})

    def test_instruction_window_rejects_missing_duplicate_and_wrong_register(self):
        text = gzip.decompress((module.ROOT / module.CHAD).read_bytes()).decode()
        module.site(text, module.CHAD_SEQUENCE)
        for changed in (text.replace('Push register5', 'Push register4'),
                        text.replace('CallMethod', 'CallFunction'),
                        text.replace('Pop', 'Return'), text + '\n' + module.CHAD_SEQUENCE):
            with self.assertRaises(ValueError):
                module.site(changed, module.CHAD_SEQUENCE)

    def test_static_coordinates_are_not_pc_addresses(self):
        chad = self.report['sites']['chad']
        self.assertIn('NOT executed PC', chad['coordinate_kind'])
        instructions = chad['instructions']
        self.assertEqual([r['instruction'] for r in instructions[4:]],
                         ['CallMethod', 'Pop', 'Push register5', 'Push "post"', 'Push 1', 'SetMember'])
        self.assertEqual([r['line'] for r in instructions], list(range(4444, 4454)))


if __name__ == '__main__':
    unittest.main()
