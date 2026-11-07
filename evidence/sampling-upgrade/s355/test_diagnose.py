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
    spec = importlib.util.spec_from_file_location('s355_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


d = load('diagnose')
e = load('extract_route')


class DiagnosisTests(unittest.TestCase):
    def test_wrong_binary_rejected_before_derivation(self):
        with self.assertRaises(ValueError):
            e.extract((d.ROOT / 'game/main.swf').read_bytes(), b'wrong binary')

    def test_route_mutations_rejected(self):
        record = json.loads((HERE / 'caller-route.json').read_text())
        for key, value in [('binary_sha256', 'wrong'), ('numeric_dispatch', {}),
                           ('loaded_frame_entry_route', 'invented'),
                           ('independent_outer_lifetime', 'invented'),
                           ('module_uuid', 'wrong'), ('new_native_prefix', {})]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                d.audit_route(dict(record, **{key: value}))

    def test_actual_caller_is_distinct_from_prior_numeric_candidate(self):
        route = d.audit_route(json.loads((HERE / 'caller-route.json').read_text()))
        caller = route['caller']
        self.assertEqual(caller['opcode'], 0x52)
        self.assertEqual(caller['function_body_end_exclusive'], 662)
        self.assertEqual(caller['call_offset'], 660)
        self.assertEqual(caller['constant_pool'][22], '个')
        self.assertEqual(route['numeric_dispatch']['target'], 0x124c2b)
        self.assertEqual(route['first_branch_target'], 0x126537)
        self.assertIsNone(route['loaded_frame_entry_route'])
        self.assertIsNone(route['independent_outer_lifetime'])

    def test_original_substitution_rejected(self):
        with self.assertRaises(ValueError):
            e.source_callsite(b'wrong original')

    def test_operand_and_function_mutations_rejected(self):
        record = json.loads((HERE / 'caller-route.json').read_text())
        for key, value in [('opcode', 0x9f), ('call_offset', 627),
                           ('constant_pool', []), ('function_body_end_exclusive', 660),
                           ('loaded_caller_association', 'invented')]:
            changed = copy.deepcopy(record)
            changed['caller'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                d.audit_route(changed)

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
                self.assertIn(d.GATES[flag] if flag else 'S355_DIAGNOSIS_OK', result.stdout)
                self.assertFalse(json.loads(output.read_text())['production_admitted'])


if __name__ == '__main__':
    unittest.main()
