"""Protect the first-control-transfer evidence boundary and complete retained replay."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s363_diagnose', HERE / 'diagnose.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = d.replay()
        cls.native = json.loads((HERE / 'native-prefix.json').read_text())

    def test_first_transfer_operands_and_stop(self):
        audit = d.audit(self.native, self.prior)
        self.assertEqual(audit['taken_target'], 0xd2290)
        self.assertEqual(audit['fallthrough'], 0xd2288)
        self.assertEqual(audit['new_prefix_bytes'], 11)
        self.assertEqual(audit['successor_bytes_read'], 0)
        self.assertEqual(audit['condition'], '(incoming RBX & 7) != 7')
        self.assertEqual([r['address'] for r in audit['instructions']],
                         [0xd227d, 0xd227f, 0xd2282, 0xd2286])

    def test_every_rehashed_byte_mutation_rejected(self):
        for offset in range(11):
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
            pin.write_text(json.dumps({'evidence/sampling-upgrade/s354/diagnosis.json': 'wrong'}))
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
        self.assertFalse(report['audit']['successor_code_expanded'])
        self.assertIsNone(report['audit']['actual_target'])


if __name__ == '__main__':
    unittest.main()
