"""Protect the signed-offset evidence boundary and complete retained replay."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s354_diagnose', HERE / 'diagnose.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = d.replay()
        cls.native = json.loads((HERE / 'native-table.json').read_text())

    def test_signed_offsets_use_table_base_not_entry_address(self):
        audit = d.audit(self.native, self.prior)
        self.assertEqual(len(audit['rows']), 19)
        for row in audit['rows']:
            unsigned = int.from_bytes(bytes.fromhex(row['hex']), 'little')
            self.assertGreaterEqual(unsigned, 2**31)
            self.assertEqual(row['destination'], 0xd2540 + unsigned - 2**32)
            self.assertIsNone(row['actual_execution'])
        self.assertEqual(audit['destination_groups']['0xd2482'], [3, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17])
        self.assertEqual(audit['unique_destinations'], 8)

    def test_every_rehashed_byte_mutation_rejected(self):
        for offset in range(76):
            native = copy.deepcopy(self.native)
            raw = bytearray.fromhex(native['hex'])
            raw[offset] ^= 1
            native.update(hex=raw.hex(), sha256=d.sha(raw))
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                d.audit(native, self.prior)

    def test_bounds_provenance_extra_fields_and_proof_rejected(self):
        for key in self.native:
            native = copy.deepcopy(self.native)
            native[key] = native[key] + 1 if isinstance(native[key], int) else '00'
            with self.subTest(key=key), self.assertRaises(ValueError):
                d.audit(native, self.prior)
        with self.assertRaises(ValueError):
            d.audit(self.native | {'actual_execution': True}, self.prior)

    def test_entire_prior_replay_is_required(self):
        for key, value in [('production_admitted', True), ('observations', {}), ('blocker', 'changed')]:
            prior = self.prior | {key: value}
            with self.assertRaises(ValueError):
                d.audit(self.native, prior)
            with patch.object(d, 'load_prior') as loader:
                loader.return_value.diagnose.return_value = prior
                with self.assertRaises(ValueError):
                    d.replay()

    def test_changed_pin_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            pin = Path(tmp) / 'pins.json'
            pin.write_text(json.dumps({'evidence/sampling-upgrade/s345/diagnosis.json': 'wrong'}))
            with self.assertRaises(ValueError):
                d.verify_pins(pin)

    def test_unproved_stays_unproved(self):
        report = d.diagnose()
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['native_parity_proven'])
        self.assertEqual(report['m0_02_status'], 'pending')
        self.assertEqual(report['other_ranks_executed'], [])
        self.assertEqual(report['retained'], self.prior)
        self.assertTrue(all(v is None for v in report['observations'].values()))
        self.assertTrue(all(not v['proved'] for v in report['gates'].values()))
        self.assertFalse(report['audit']['destination_code_expanded'])
        self.assertIsNone(report['audit']['actual_target'])


if __name__ == '__main__':
    unittest.main()
