"""Protect native byte derivation, coordinate separation and fail-closed gates."""
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
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('s303', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class NativeCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.diagnose()
        cls.native = json.loads((HERE / 'native-audit.json').read_text())

    def changed_region(self, name, offset, value):
        native = copy.deepcopy(self.native)
        region = native['regions'][name]
        data = bytearray.fromhex(region['hex'])
        data[offset] = value
        region['hex'], region['sha256'] = data.hex(), audit.sha(data)
        return native

    def test_derived_targets(self):
        candidate = self.report['native_candidate']
        self.assertEqual(candidate['module_uuid'], '067c4cfe5b2a3424aaa01fae2df056eb')
        self.assertEqual([r['target_relative'] for r in candidate['targets']],
                         [0x124c2b, 0x125cab, 0x125294])
        self.assertEqual(candidate['dispatch_table_relative'], 0x12cf44)

    def test_cursor_increment_mutation_rejected_even_with_region_hash(self):
        native = self.changed_region('fetch_and_dispatch', 0x124786 - 0x124726, 2)
        with self.assertRaisesRegex(ValueError, 'derivation bytes changed'):
            audit.derive(native)

    def test_dispatch_target_mutation_rejected_even_with_region_hash(self):
        native = self.changed_region('dispatch_table', 4 * (0x17 - 4), 0x68)
        with self.assertRaisesRegex(ValueError, 'dispatch target differs'):
            audit.derive(native)

    def test_stack_layout_mutation_rejected(self):
        native = self.changed_region('pop_candidate', 10, 0x21)
        with self.assertRaisesRegex(ValueError, 'derivation bytes changed'):
            audit.derive(native)

    def test_file_coordinate_mutation_rejected(self):
        native = copy.deepcopy(self.native)
        native['regions']['dispatch_table']['file_offset'] += 1
        with self.assertRaisesRegex(ValueError, 'mapping differs'):
            audit.derive(native)

    def test_truncated_header_rejected(self):
        with self.assertRaisesRegex(ValueError, 'truncated'):
            audit.macho(bytes.fromhex(self.native['module']['header_hex'])[:-1])

    def test_zero_fill_is_not_file_backed(self):
        with self.assertRaisesRegex(ValueError, 'file-backed'):
            audit.file_offset(self.native['module'], 0x10, 8)

    def test_missing_region_rejected(self):
        native = copy.deepcopy(self.native)
        del native['regions']['pop_candidate']
        with self.assertRaisesRegex(ValueError, 'uncovered'):
            audit.derive(native)

    def test_static_candidate_does_not_supply_live_proof(self):
        self.assertTrue(all(v is None for v in self.report['observations'].values()))
        self.assertTrue(all(not g['proved'] for g in self.report['gates'].values()))
        self.assertEqual(self.report['historical']['events'], 9493)
        worker = self.report['retained_worker']
        self.assertEqual(worker['ambiguous_file_offset'], 589408)
        self.assertEqual(worker['body_occurrences_in_archived_swf'], 1)
        self.assertIsNone(self.report['native_candidate']['candidate_layout']['register4_location'])
        self.assertFalse(self.report['production_admitted'])
        self.assertFalse(self.report['native_parity_proven'])
        self.assertEqual(self.report['scope'], 'AFTER-s299 rank #4 only')
        for field in ('new_builds', 'new_player_launches', 'new_captures', 'new_name_queries'):
            self.assertEqual(self.report[field], 0)

    def test_custody_tamper_rejected(self):
        original = Path.read_bytes
        def changed(path):
            data = original(path)
            return data + b'changed' if path == HERE / 'native-audit.json' else data
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'locked input changed'):
                audit.diagnose()

    def test_all_proof_gates_exit_one(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, code in audit.GATES.items():
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'),
                    '--output', str(Path(directory) / 'report.json'), '--require-' + name],
                    capture_output=True, text=True, cwd=audit.ROOT)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stderr)


if __name__ == '__main__':
    unittest.main()
