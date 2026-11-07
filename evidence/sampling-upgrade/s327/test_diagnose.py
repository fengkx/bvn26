"""Protect byte custody, caller relations and honest unproved boundaries."""
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
spec = importlib.util.spec_from_file_location('s327_diagnose', HERE / 'diagnose.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = d.replay()
        cls.native = json.loads((HERE / 'native-audit.json').read_text())
        cls.log = (HERE / 'callee-entry.txt').read_bytes()

    def test_byte_derived_accesses_and_frontier(self):
        report = d.audit(self.native, self.log, self.prior)
        nodes = {n['address']: n for n in report['instructions']}
        # Instruction bytes independently fix the direct store/load widths and registers.
        self.assertEqual(nodes[0xd222c]['hex'], '49c7042402000000')
        self.assertEqual(nodes[0xd2234]['hex'], '498b1f')
        self.assertEqual(report['bytes_audited'], 68)
        self.assertEqual(report['first_frontier']['target'], 0xd2254)
        self.assertEqual(report['first_frontier']['fallthrough'], 0xd2244)
        self.assertFalse(report['first_frontier']['successors_expanded'])
        self.assertEqual(report['explicit_calls'], 0)
        self.assertEqual(report['machine_returns'], 0)

    def test_resealed_mutated_bytes_rejected(self):
        for offset in (0x14, 0x17, 0x1a, 0x2c, 0x34, 0x42, 0x43):
            with self.subTest(offset=offset):
                native = copy.deepcopy(self.native)
                raw = bytearray.fromhex(native['hex'])
                raw[offset] ^= 1
                native['hex'] = raw.hex()
                native['sha256'] = d.sha(raw)
                with self.assertRaises(ValueError):
                    d.audit(native, self.log, self.prior)

    def test_wrong_binary_or_bounds_rejected(self):
        for key in ('binary_sha256', 'module_uuid', 'binary_size', 'image_base', 'end_exclusive', 'file_offset'):
            with self.subTest(key=key):
                native = copy.deepcopy(self.native)
                native[key] = 'wrong' if isinstance(native[key], str) else native[key] + 1
                with self.assertRaises(ValueError):
                    d.audit(native, self.log, self.prior)

    def test_changed_disassembly_rejected(self):
        for log in (self.log.replace(b'[r12]', b'[r14]'), self.log.replace(b'jne', b'jmp'), self.log[:-1]):
            with self.assertRaises(ValueError):
                d.audit(self.native, log, self.prior)

    def test_caller_argument_or_target_substitution_rejected(self):
        for address, key, value in ((0x12696b, 'operands', 'rdi, [rbp - 0x60]'),
                                    (0x126972, 'operands', 'rdx, [rbp - 0x550]'),
                                    (0x126976, 'operands', 'rsi, r14'),
                                    (0x126979, 'target', 0x5f50)):
            prior = copy.deepcopy(self.prior)
            next(n for n in prior['path_audit']['instructions'] if n['address'] == address)[key] = value
            with self.assertRaises(ValueError):
                d.audit(self.native, self.log, prior)

    def test_entire_prior_replay_including_proof_promotion(self):
        for key, value in (('production_admitted', True), ('retained_invocation', {}),
                           ('blocker', 'changed outside the new cut')):
            prior = copy.deepcopy(self.prior)
            prior[key] = value
            with patch.object(d, 'load_prior') as loader:
                loader.return_value.diagnose.return_value = prior
                with self.assertRaises(ValueError):
                    d.replay()

    def test_unknowns_stay_unknown(self):
        report = d.diagnose()
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['native_parity_proven'])
        self.assertEqual(report['m0_02_status'], 'pending')
        self.assertEqual(report['other_ranks_executed'], [])
        self.assertTrue(all(v is None for v in report['observations'].values()))
        self.assertTrue(all(not g['proved'] for g in report['gates'].values()))
        self.assertIsNone(report['audit']['alias_relations'])
        self.assertFalse(report['audit']['callee_return_proven'])

    def test_cli_base_and_all_proof_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'diagnosis.json'
            for flag in (None, *d.GATES):
                command = [sys.executable, str(HERE / 'diagnose.py'), '--output', str(output)]
                if flag:
                    command.append('--require-' + flag)
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1 if flag else 0, result.stderr)
                self.assertIn(d.GATES[flag] if flag else 'S327_DIAGNOSIS_OK', result.stdout)
                self.assertFalse(json.loads(output.read_text())['production_admitted'])


if __name__ == '__main__':
    unittest.main()
