"""Reject provenance substitutions and promotion of absent clock observations."""
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


def load(name):
    spec = importlib.util.spec_from_file_location('s337_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


d = load('diagnose')
e = load('extract_native')


class DiagnosisTests(unittest.TestCase):
    def test_exact_byte_search_bounds(self):
        self.assertEqual(e.occurrences(b'gotoAndStop\0x\0gotoAndStop\0', b'\0gotoAndStop\0'), [13])
        self.assertEqual(e.occurrences(b'aaa', b'aa'), [0, 1])

    def test_wrong_binary_rejected_before_search(self):
        with self.assertRaises(ValueError):
            e.extract(b'\0gotoAndStop\0')

    def test_search_provenance_and_proof_mutations_rejected(self):
        record = json.loads((HERE / 'native-search.json').read_text())
        for key, value in [('binary_sha256', 'wrong'), ('matches', [{'file_offset': 1}]),
                           ('native_entry_site', 123), ('outer_instance_lifetime_channel', 'helper'),
                           ('new_attaches', 1), ('module_uuid', 'wrong')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                d.audit_search(dict(record, **{key: value}))

    def test_complete_prior_replay_rejects_promotion_and_drift(self):
        prior = d.replay()
        for key, value in [('production_admitted', True), ('live_entry_resolver', 123),
                           ('blocker', 'changed'), ('qualification_matrix', [])]:
            changed = copy.deepcopy(prior)
            changed[key] = value
            with patch.object(d, 'load_prior') as loader:
                loader.return_value.diagnose.return_value = changed
                with self.assertRaises(ValueError):
                    d.replay()

    def test_pin_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'pins.json'
            path.write_text(json.dumps({'game/main.swf': 'wrong'}))
            with self.assertRaises(ValueError):
                d.verify_pins(path)

    def test_unknowns_remain_unknown(self):
        report = d.diagnose()
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['native_parity_proven'])
        self.assertEqual(report['m0_02_status'], 'pending')
        self.assertIsNone(report['live_entry_resolver'])
        self.assertIsNone(report['live_instance_resolver'])
        self.assertEqual(report['independent_observations_new'], [])
        self.assertFalse(report['fresh_capture_eligible'])
        self.assertTrue(all(r['qualified'] is None and not r['executed'] for r in report['controls'].values()))
        self.assertEqual(report['other_ranks_executed'], [])

    def test_cli_all_gates(self):
        with tempfile.TemporaryDirectory() as temp:
            for flag in (None, *d.GATES):
                output = Path(temp) / 'diagnosis.json'
                command = [sys.executable, str(HERE / 'diagnose.py'), '--output', str(output)]
                if flag:
                    command += ['--require-' + flag]
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, int(flag is not None), result.stderr)
                self.assertIn(d.GATES[flag] if flag else 'S337_DIAGNOSIS_OK', result.stdout)
                self.assertFalse(json.loads(output.read_text())['production_admitted'])


if __name__ == '__main__':
    unittest.main()
