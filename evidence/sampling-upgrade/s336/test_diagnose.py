"""Protect byte-derived frontiers, full retained replay and honest proof gates."""
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
spec = importlib.util.spec_from_file_location('s336_diagnose', HERE / 'diagnose.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = d.replay()
        cls.native = json.loads((HERE / 'native-audit.json').read_text())
        cls.logs = {w['start']: (HERE / w['log']).read_bytes() for w in cls.native['windows']}

    def test_byte_derived_read_join_and_unsigned_frontier(self):
        report = d.audit(self.native, self.logs, self.prior)
        nodes = {n['address']: n for n in report['windows'][0]['instructions']}
        self.assertEqual(nodes[0xd2247]['hex'], '4883e0f8')
        self.assertEqual(nodes[0xd224b]['hex'], '488b4018')
        self.assertEqual(nodes[0xd225a]['hex'], '0f45c1')
        self.assertEqual(nodes[0xd2267]['hex'], '0f8715020000')
        self.assertEqual(report['unique_bytes_audited'], 41)
        self.assertEqual(report['unique_instructions'], 12)
        self.assertEqual(report['overlap_bytes'], 25)
        self.assertEqual(report['join'], 0xd2254)
        self.assertEqual(report['next_frontier']['target'], 0xd2482)
        self.assertEqual(report['next_frontier']['fallthrough'], 0xd226d)
        self.assertFalse(report['next_frontier']['successors_expanded'])
        self.assertEqual(report['explicit_calls'], 0)
        self.assertEqual(report['machine_returns'], 0)

    def test_resealed_mutated_bytes_rejected(self):
        for i, window in enumerate(self.native['windows']):
            for offset in range(len(bytes.fromhex(window['hex']))):
                with self.subTest(window=i, offset=offset):
                    native = copy.deepcopy(self.native)
                    raw = bytearray.fromhex(window['hex'])
                    raw[offset] ^= 1
                    native['windows'][i].update(hex=raw.hex(), sha256=d.sha(raw))
                    with self.assertRaises(ValueError):
                        d.audit(native, self.logs, self.prior)

    def test_wrong_provenance_bounds_or_window_set_rejected(self):
        for key in ('binary_sha256', 'module_uuid', 'binary_size', 'image_base'):
            native = copy.deepcopy(self.native)
            native[key] = 'wrong' if isinstance(native[key], str) else native[key]+1
            with self.assertRaises(ValueError):
                d.audit(native, self.logs, self.prior)
        for key in ('end_exclusive', 'file_offset', 'exit_code'):
            native = copy.deepcopy(self.native)
            native['windows'][0][key] += 1
            with self.assertRaises(ValueError):
                d.audit(native, self.logs, self.prior)
        for windows in ([], self.native['windows'][:1], self.native['windows'][::-1], self.native['windows']*2):
            with self.assertRaises(ValueError):
                d.audit(dict(self.native, windows=windows), self.logs, self.prior)

    def test_changed_disassembly_rejected(self):
        for start, log in self.logs.items():
            for changed in (log.replace(b'ja\t', b'jg\t'), log.replace(b'cmovne', b'cmove'), log[:-1]):
                with self.assertRaises(ValueError):
                    d.audit(self.native, self.logs | {start: changed}, self.prior)

    def test_retained_frontier_and_argument_substitution_rejected(self):
        for key, value in (('first_frontier', {}), ('incoming_argument_relations', []), ('predicate', 'different')):
            prior = copy.deepcopy(self.prior)
            prior['audit'][key] = value
            with self.assertRaises(ValueError):
                d.audit(self.native, self.logs, prior)

    def test_entire_prior_replay_including_proof_promotion(self):
        for key, value in (('production_admitted', True), ('observations', {}),
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

    def test_input_and_ranking_pin_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            pin = Path(temp) / 'pins.json'
            pin.write_text(json.dumps({'evidence/sampling-upgrade/s327/diagnosis.json': 'wrong'}))
            with self.assertRaises(ValueError):
                d.verify_pins(pin)

    def test_cli_base_and_all_proof_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'diagnosis.json'
            for flag in (None, *d.GATES):
                command = [sys.executable, str(HERE / 'diagnose.py'), '--output', str(output)]
                if flag:
                    command.append('--require-' + flag)
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1 if flag else 0, result.stderr)
                self.assertIn(d.GATES[flag] if flag else 'S336_DIAGNOSIS_OK', result.stdout)
                self.assertFalse(json.loads(output.read_text())['production_admitted'])


if __name__ == '__main__':
    unittest.main()
