"""A positive dynamic-removal control must not become Chad exit-model proof."""
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parents[2] / 'evidence/sampling-upgrade/s263'
spec = importlib.util.spec_from_file_location('s263_diagnose', HERE / 'diagnose.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ChadRegisterControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode().splitlines()
        cls.report = module.diagnose()

    def test_recompute_and_keep_exact_context_unproved(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        for key in ('production_admitted', 'native_parity_proven', 'exit_model_fix_proved',
                    'executed_pc_trace', 'exact_chad_context_invalidation_access_proved'):
            self.assertFalse(self.report[key])
        self.assertTrue(self.report['dynamic_receiver_removal_register_access_observed'])
        self.assertEqual(self.report['actor_comparison']['rows'], 122)
        self.assertTrue(self.report['chad_swf_unchanged'])

    def test_independent_slot_observation_precedes_successful_write(self):
        retain, remove = module.controls(self.lines)
        self.assertEqual((retain['empty_at_boundary'], remove['empty_at_boundary']), ('false', 'true'))
        self.assertEqual((retain['post'], remove['post']), ('1', '1'))
        self.assertEqual(self.report['lifecycle']['missing_boundaries'],
                         ['goto_after', 'callee_exit', 'caller_after'])

    def test_absent_duplicate_or_changed_control_rejected(self):
        selected = next(line for line in self.lines if '|s263_register_control|remove,' in line)
        variants = [[line for line in self.lines if line != selected], self.lines + [selected]]
        for replacement in ('remove,1,true,true,false,1,1,true',
                            'remove,1,true,true,true,1,0,true',
                            'remove,1,false,true,true,1,1,true',
                            'remove,1,true,true,true,1,1,false'):
            variants.append([line.rsplit('|', 1)[0] + '|' + replacement if line == selected else line
                             for line in self.lines])
        for lines in variants:
            with self.assertRaises(ValueError):
                module.controls(lines)

    def test_compiled_witness_cannot_be_target_lookup_or_renamed(self):
        text = gzip.decompress((HERE / 'pcode/main/frame_1/DoAction.pcode.gz').read_bytes()).decode()
        module.compiled_control(text)
        for altered in (text.replace('Push "post"', 'Push "other"'),
                        text.replace('StoreRegister 4', 'StoreRegister 9')):
            with self.assertRaises(ValueError):
                module.compiled_control(altered)


if __name__ == '__main__':
    unittest.main()
