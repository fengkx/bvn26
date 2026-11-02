"""Protect byte-bounded relations and reject unsupported ownership promotion."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s311_diagnose', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.diagnose()
        cls.native = json.loads((HERE.parent / 's303/native-audit.json').read_text())

    def mutate(self, address):
        native = copy.deepcopy(self.native)
        region = next(r for r in native['regions'].values()
                      if r['module_relative'] <= address < r['module_relative'] + r['size'])
        raw = bytearray.fromhex(region['hex'])
        raw[address - region['module_relative']] ^= 1
        region['hex'] = raw.hex()
        region['sha256'] = hashlib.sha256(raw).hexdigest()
        return native

    def test_full_diagnosis_reproducible(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual(self.report['historical']['events'], 9493)
        self.assertEqual(self.report['retained_worker']['ambiguous_file_offset'], 589408)

    def test_three_transfers_and_external_edges(self):
        layout = self.report['layout_audit']
        self.assertEqual([r['destination_frame_offset'] for r in layout['slot_transfers']],
                         [-0x60, -0x68, -0x548])
        self.assertEqual([r['target'] for r in layout['external_edges']],
                         [0x1264b9, 0x1264c8, 0x1264d0, 0x1264db, 0x98b8e0, 0x12f580])
        self.assertTrue(all(not r['target_body_covered'] for r in layout['external_edges']))

    def test_conditional_carrier_origin_mutations_rejected(self):
        for address in (0x12479e, 0x1247b4, 0x124969, 0x124973):
            with self.subTest(address=hex(address)), self.assertRaisesRegex(ValueError, 'layout bytes'):
                audit.bound_layout(self.mutate(address))

    def test_value_mask_and_indirection_mutations_rejected(self):
        for address in (0x124991, 0x1249a0, 0x1249a4, 0x1249ac, 0x1249af, 0x1249b2, 0x1249f5):
            with self.subTest(address=hex(address)), self.assertRaisesRegex(ValueError, 'layout bytes'):
                audit.bound_layout(self.mutate(address))

    def test_slot_copies_clears_and_guards_rejected(self):
        for address in (0x124c40, 0x124c56, 0x124c5a, 0x124c5f, 0x124c6f,
                        0x124c8a, 0x124c98, 0x124cb4, 0x124cc1):
            with self.subTest(address=hex(address)), self.assertRaisesRegex(ValueError, 'layout bytes'):
                audit.bound_layout(self.mutate(address))

    def test_helper_arguments_and_restore_mutations_rejected(self):
        for address in (0x124a1b, 0x124a21, 0x124a2e, 0x124a33, 0x124a48, 0x124a65):
            with self.subTest(address=hex(address)), self.assertRaisesRegex(ValueError, 'layout bytes'):
                audit.bound_layout(self.mutate(address))

    def test_custody_mutation_rejected(self):
        original = Path.read_bytes
        def changed(path):
            raw = original(path)
            return raw + b'changed' if path.name == 'native-audit.json' else raw
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'locked input changed'):
                audit.diagnose()

    def test_local_layout_is_not_activation_or_value_ownership(self):
        layout = self.report['layout_audit']
        self.assertEqual(len({r['origin'] for r in layout['ownership_boundaries']}), 3)
        self.assertTrue(all(r['activation_owner'] is None for r in layout['ownership_boundaries']))
        for key in ('avm_type_names', 'defining_scope', 'register4_location', 'allocation_generation',
                    'activation_identity', 'stack_carrier_alias_relation', 'helper_preservation'):
            self.assertIsNone(layout[key])
        self.assertTrue(all(v is None for v in self.report['observations'].values()))
        self.assertTrue(all(not g['proved'] for g in self.report['gates'].values()))

    def test_scope_and_admission(self):
        self.assertEqual(self.report['scope'], 'AFTER-s308 rank #3 only')
        self.assertFalse(self.report['production_admitted'])
        self.assertFalse(self.report['native_parity_proven'])
        self.assertEqual(self.report['m0_02_status'], 'pending')
        self.assertEqual(self.report['other_ranks_executed'], [])
        for field in ('new_builds', 'new_player_launches', 'new_captures', 'new_memory_reads'):
            self.assertEqual(self.report[field], 0)

    def test_all_proof_gates_exit_one(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, code in audit.GATES.items():
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'),
                    '--output', str(Path(directory) / 'report.json'), '--require-' + name],
                    capture_output=True, text=True, cwd=audit.ROOT)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stdout)


if __name__ == '__main__':
    unittest.main()
