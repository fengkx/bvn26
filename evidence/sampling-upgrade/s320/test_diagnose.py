"""Lock byte custody, first opaque boundaries and non-admission."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s320_diagnose', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class FrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = json.loads((HERE / 'native-audit.json').read_text())
        cls.report = audit.diagnose()

    def test_reproduction(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual(self.report['historical']['events'], 9493)
        self.assertEqual(self.report['path_audit']['bytes_audited'], 1049)

    def test_stack_branches_stop_at_first_opaque_calls(self):
        rows = self.report['path_audit']['first_frontiers'][:4]
        self.assertEqual([r['entry'] for r in rows], [0x1264b9, 0x1264c8, 0x1264d0, 0x1264db])
        for row in rows:
            self.assertEqual({s['address'] for s in row['first_boundaries']}, {0x126979, 0x126988})
            self.assertTrue(all(s['kind'] == 'opaque_call' for s in row['first_boundaries']))
            for stop in row['first_boundaries']:
                self.assertEqual(stop['witness_path'][0], row['entry'])
                self.assertEqual(stop['witness_path'][-1], stop['address'])
                self.assertNotIn(0x126979, stop['witness_path'][:-1])

    def test_all_nested_calls_and_machine_returns_retained(self):
        paths = self.report['path_audit']
        self.assertEqual([(c['site'], c['target']) for c in paths['calls']],
                         [(0x126979, 0xd2200), (0x126988, 0x5f50),
                          (0x12f63b, 0x9929e0), (0x12f6f6, 0x98da30),
                          (0x98b93b, 0x994170), (0x98b9e6, 0x994170)])
        self.assertEqual(paths['machine_returns'], [0x12f707, 0x98ba8b])
        self.assertIn({'site': 0x98ba21, 'target': 0x98b9b0}, paths['backward_edges'])
        self.assertFalse(paths['termination_proven'])
        self.assertFalse(paths['path_feasibility_proven'])
        self.assertIsNone(paths['exceptional_exits'])

    def test_rehashed_operand_and_branch_mutations_rejected(self):
        for name in audit.PINS:
            for index in (0, self.native['regions'][name]['size'] // 2,
                          self.native['regions'][name]['size'] - 1):
                changed = copy.deepcopy(self.native)
                region = changed['regions'][name]
                raw = bytearray.fromhex(region['hex'])
                raw[index] ^= 1
                region['hex'], region['sha256'] = raw.hex(), audit.sha(raw)
                with self.subTest(name=name, index=index), self.assertRaisesRegex(ValueError, 'fixed region'):
                    audit.audit_paths(changed)

    def test_module_and_window_changes_rejected(self):
        for field in ('binary_sha256', 'module_uuid', 'image_base', 'binary_size'):
            changed = copy.deepcopy(self.native)
            changed[field] = None
            with self.assertRaisesRegex(ValueError, 'native custody'):
                audit.audit_paths(changed)
        changed = copy.deepcopy(self.native)
        changed['regions']['extra'] = {}
        with self.assertRaisesRegex(ValueError, 'region scope'):
            audit.audit_paths(changed)

    def test_disassembly_custody_rejected(self):
        original = Path.read_bytes
        def changed(path):
            raw = original(path)
            return raw + b'changed' if path.name == 'carrier_store.txt' else raw
        with patch.object(Path, 'read_bytes', changed), self.assertRaisesRegex(ValueError, 'disassembly changed'):
            audit.audit_paths(self.native)

    def test_prior_custody_rejected(self):
        original = Path.read_bytes
        def changed(path):
            raw = original(path)
            return raw + b'changed' if path.parent.name == 's311' else raw
        with patch.object(Path, 'read_bytes', changed), self.assertRaisesRegex(ValueError, 'locked input changed'):
            audit.diagnose()

    def test_no_ownership_or_live_promotion(self):
        for key in ('activation_identity', 'defining_scope', 'register4_location',
                    'stack_carrier_descriptor_alias_relation', 'allocation_generation',
                    'helper_preservation', 'live_module_binding', 'loaded_worker_binding',
                    'measured_cursor', 'retained_invocation'):
            self.assertIsNone(self.report[key])
        for key in ('production_admitted', 'native_parity_proven', 'exact_continuation_proved',
                    'prior_results_are_new_progress'):
            self.assertFalse(self.report[key])
        self.assertEqual(self.report['scope'], 'AFTER-s317 rank #3 only')
        self.assertEqual(self.report['m0_02_status'], 'pending')
        self.assertEqual(self.report['other_ranks_executed'], [])

    def test_proof_flags_fail_individually(self):
        with tempfile.TemporaryDirectory() as directory:
            for flag, code in audit.GATES.items():
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'),
                                         '--output', str(Path(directory) / 'out.json'),
                                         '--require-' + flag], capture_output=True, text=True, cwd=audit.ROOT)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stdout)


if __name__ == '__main__':
    unittest.main()
