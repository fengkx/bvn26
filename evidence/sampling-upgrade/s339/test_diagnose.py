"""Protect absent measurements from accidental promotion and provenance drift."""
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
spec = importlib.util.spec_from_file_location('s339', HERE / 'diagnose.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class EvidenceTests(unittest.TestCase):
    def test_unknowns_remain_unknown(self):
        result = d.diagnose()
        self.assertFalse(result['production_admitted'])
        self.assertFalse(result['native_parity_proven'])
        self.assertEqual(result['m0_02_status'], 'pending')
        self.assertEqual(result['independent_native_observations'], 0)
        self.assertEqual(result['other_ranks_executed'], [])
        for row in result['attempt']['boundaries']:
            self.assertTrue(all(v is None for k, v in row.items() if k != 'boundary'))
        self.assertTrue(all(not g['proved'] for g in result['gates'].values()))

    def test_no_static_bytes_zero_or_mutable_slot_as_live_proof(self):
        record = d.expected_attempt()
        substitutions = {
            'executed_caller': '0x100108f68',
            'actual_p1_consumer': 'static-candidate',
            'immutable_request_generation': 'mutable-stream-slot',
            'returned_buffer_ranges': [{'byte': 0, 'source': 'initialized-local'}],
            'consumed_buffer_ranges': [{'source': 'disk-file'}],
            'target_before_inline_advance': '_root.game.p1',
            'executed_read_return': 0,
            'partial_or_failed_read_behavior': 'assumed-success',
            'uninterrupted_lifetime': True,
            'normal_association_qualified': True,
            'wrong_resource_control_executed': True,
            'independent_observations': ['breakpoint-hit-only'],
        }
        for key, value in substitutions.items():
            with self.subTest(key=key), self.assertRaises(ValueError):
                d.audit_attempt(dict(record, **{key: value}))

    def test_no_zero_range_or_missing_boundary_promoted(self):
        for index in range(len(d.BOUNDARIES)):
            record = d.expected_attempt()
            record['boundaries'][index]['range_measurement'] = 0
            with self.subTest(index=index), self.assertRaises(ValueError):
                d.audit_attempt(record)
        record = d.expected_attempt()
        record['boundaries'].pop()
        with self.assertRaises(ValueError):
            d.audit_attempt(record)

    def test_complete_replay_rejects_changed_prior(self):
        original = d.replay()
        for key, value in [('production_admitted', True), ('bindings', []),
                           ('blocker', 'changed')]:
            changed = copy.deepcopy(original)
            changed[key] = value
            with patch.object(d, 'load_prior') as loader:
                loader.return_value.diagnose.return_value = changed
                with self.assertRaises(ValueError):
                    d.replay()

    def test_changed_pinned_input_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'pins.json'
            path.write_text(json.dumps({'game/main.swf': 'wrong'}))
            with self.assertRaises(ValueError):
                d.verify_pins(path)

    def test_cli_gates_individually_and_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            for gates in [(), *((gate,) for gate in d.GATES), d.GATES]:
                output = Path(tmp) / 'result.json'
                command = [sys.executable, str(HERE / 'diagnose.py'), '--output', str(output)]
                command += ['--require-' + gate for gate in gates]
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, int(bool(gates)), result.stderr)
                self.assertFalse(json.loads(output.read_text())['production_admitted'])
                for gate in gates:
                    self.assertIn('S339_' + gate.upper().replace('-', '_') + '_UNPROVED', result.stdout)


if __name__ == '__main__':
    unittest.main()
