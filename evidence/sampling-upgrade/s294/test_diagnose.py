"""Protect byte provenance and fail-closed observer qualification."""
import copy
import importlib.util
import struct
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s294_diagnosis', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class QualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.diagnose()
        cls.original = cls.report['compiled_nested_functions']['original']
        raw = (audit.ROOT / 'game/fighter/yulong.swf').read_bytes()
        cls.raw = b'FWS' + raw[3:8] + zlib.decompress(raw[8:])

    def test_locked_replay_and_unproved_observations(self):
        self.assertTrue(self.report['locked_s285_reproduced'])
        self.assertEqual(self.report['retained_events'], 5214)
        for field in ('production_admitted', 'native_parity_proven', 'observer_qualified',
                      'direct_removal_dispatch_proved', 'nested_entry_proved',
                      'complete_activation_operand_preservation_proved'):
            self.assertIs(self.report[field], False)
        self.assertTrue(all(v is None for v in self.report['observations'].values()))
        self.assertEqual(self.report['paired_controls'], 0)

    def test_complete_function_inventory(self):
        self.assertEqual([f['name'] for f in self.original['functions']], audit.FUNCTIONS)
        for f in self.original['functions']:
            self.assertEqual(len(bytes.fromhex(f['body_hex'])), f['body_length'])
            self.assertEqual(audit.sha(bytes.fromhex(f['body_hex'])), f['body_sha256'])
            self.assertEqual(f['instructions'][0]['offset'], f['body_offset'])
            self.assertEqual(f['instructions'][-1]['end'], f['body_offset'] + f['body_length'])

    def test_archived_activation_difference_is_visible(self):
        original = self.original['functions'][4]
        archived = self.report['compiled_nested_functions']['s275_archive']['functions'][4]
        self.assertEqual((original['name'], original['register_count']), ('getHitObj', 15))
        self.assertEqual(archived['register_count'], 9)
        self.assertEqual([p['register'] for p in original['parameters']], [9, 13, 12, 3])
        self.assertEqual([p['register'] for p in archived['parameters']], [2, 3, 4, 5])
        self.assertFalse(self.report['compiled_nested_functions']['comparison'][4]['activation_header_equal'])

    def test_register_or_parameter_changes_cannot_pass(self):
        for key, value in [('register_count', 16), ('parameters', [])]:
            changed = copy.deepcopy(self.original)
            changed['functions'][4][key] = value
            self.assertFalse(audit.compare(self.original, changed)[4]['activation_header_equal'])

    def test_pool_change_is_not_byte_equivalence(self):
        changed = copy.deepcopy(self.original)
        changed['functions'][0]['constant_pool'].append('synthetic-negative')
        self.assertFalse(audit.compare(self.original, changed)[0]['constant_pool_equal'])

    def test_reordered_functions_rejected(self):
        changed = copy.deepcopy(self.original)
        changed['functions'].reverse()
        with self.assertRaisesRegex(ValueError, 'misaligned'):
            audit.compare(self.original, changed)

    def test_truncated_swf_rejected(self):
        with self.assertRaisesRegex(ValueError, 'length mismatch'):
            audit.function_inventory(self.raw[:-1])

    def test_missing_function_rejected(self):
        data = bytearray(self.raw)
        offset = self.original['functions'][0]['definition_offset'] + 3
        data[offset] = ord('X')
        with self.assertRaisesRegex(ValueError, 'function inventory'):
            audit.function_inventory(bytes(data))

    def test_branch_into_payload_rejected(self):
        data = bytearray(self.raw)
        branch = next(r for f in self.original['functions'] for r in f['instructions'] if 'branch_target' in r)
        struct.pack_into('<h', data, branch['offset'] + 3, -1)
        with self.assertRaisesRegex(ValueError, 'instruction boundary'):
            audit.function_inventory(bytes(data))

    def test_body_overrun_rejected(self):
        data = bytearray(self.raw)
        struct.pack_into('<H', data, self.original['functions'][0]['body_offset'] - 2, 65535)
        with self.assertRaisesRegex(ValueError, 'function boundary'):
            audit.function_inventory(bytes(data))


if __name__ == '__main__':
    unittest.main()
