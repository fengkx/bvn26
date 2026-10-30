"""An authored removed-context absent write cannot establish a VM return."""
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parents[2] / 'evidence/sampling-upgrade/s266'
spec = importlib.util.spec_from_file_location('s266_diagnose', HERE / 'diagnose.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ChadDefiningContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = gzip.decompress((HERE / 'native-capture.log.gz').read_bytes()).decode().splitlines()
        cls.report = module.diagnose()

    def test_recompute_without_exit_inference(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        for key in ('production_admitted', 'native_parity_proven', 'exit_model_fix_proved',
                    'executed_pc_trace', 'exact_chad_context_invalidation_access_proved'):
            self.assertFalse(self.report[key])
        self.assertEqual(self.report['actor_comparison']['rows'], 122)
        self.assertTrue(self.report['chad_swf_unchanged'])

    def test_authored_pair_and_root_worker_are_distinct(self):
        retain, remove = module.controls(self.lines)
        self.assertEqual((retain['post'], remove['post']), ('1', '0'))
        self.assertEqual((retain['empty_at_boundary'], remove['empty_at_boundary']), ('false', 'true'))
        self.assertEqual([r['post'] for r in self.report['dynamic_controls']], ['1', '1'])
        self.assertEqual(self.report['lifecycle']['missing_boundaries'], ['goto_after', 'callee_exit', 'caller_after'])

    def test_missing_duplicate_or_wrong_slot_control_rejected(self):
        selected = next(line for line in self.lines if '|s266_authored_control|retain,' in line)
        variants = [[line for line in self.lines if line != selected], self.lines + [selected]]
        for index, value in ((3, 'false'), (4, 'false'), (5, 'true'), (7, '1'), (9, '0')):
            fields = selected.rsplit('|', 1)[1].split(',')
            fields[index] = value
            changed = selected.rsplit('|', 1)[0] + '|' + ','.join(fields)
            variants.append([changed if line == selected else line for line in self.lines])
        for lines in variants:
            with self.assertRaises(ValueError):
                module.controls(lines)

    def test_rejected_first_capture_is_not_a_positive_pair(self):
        lines = gzip.decompress((HERE / 'rejected-r01/native-capture.log.gz').read_bytes()).decode().splitlines()
        with self.assertRaises(ValueError):
            module.controls(lines)

    def test_post_write_must_remain_register_bound(self):
        text = gzip.decompress((HERE / 'worker.pcode.gz').read_bytes()).decode()
        module.compiled_worker(text)
        for changed in (text.replace('StoreRegister 4', 'StoreRegister 9'),
                        text.replace('Push "post"', 'Push "other"'),
                        text.replace('CallMethod', 'CallFunction')):
            with self.assertRaises(ValueError):
                module.compiled_worker(changed)


if __name__ == '__main__':
    unittest.main()
