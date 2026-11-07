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
spec = importlib.util.spec_from_file_location('s348', HERE / 'diagnose.py')
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
                    self.assertIn('S348_' + gate.upper().replace('-', '_') + '_UNPROVED', result.stdout)


if __name__ == '__main__':
    unittest.main()


class NativeRouteTests(unittest.TestCase):
    def test_disk_route_does_not_establish_execution(self):
        route = d.diagnose()['native_route']
        self.assertEqual(route['wrapper_call_target'], 0x498d20)
        self.assertEqual(route['retained_new_bytes'], 50)
        self.assertEqual(route['new_memory_reads'], 0)
        self.assertEqual(route['kind'], 'static_file_bytes_not_executed_or_consumed_bytes')

    def test_disassembly_covers_exact_bounded_bytes(self):
        import re
        region = d.audit_route()['regions']['exit_callee']
        cursor = 0x100000000 + region['start']
        decoded = bytearray()
        for line in (HERE / 'exit_callee.txt').read_text().splitlines():
            match = re.match(r'^([0-9a-f]+): ((?:[0-9a-f]{2} )+)', line)
            if match:
                self.assertEqual(int(match[1], 16), cursor)
                raw = bytes.fromhex(match[2])
                decoded.extend(raw)
                cursor += len(raw)
        self.assertEqual(decoded.hex(), region['hex'])
        self.assertEqual(cursor, 0x100000000 + region['end_exclusive'])

    def test_substituted_binary_rejected(self):
        spec = importlib.util.spec_from_file_location('s348_extract', HERE / 'extract_native.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaisesRegex(ValueError, 'binary differs'):
            module.extract(b'not the locked player')

    def test_changed_route_rejected_without_trusting_pins(self):
        original = json.loads((HERE / 'native-route.json').read_text())
        for key, value in [('hex', '00' * 50), ('start', 0), ('end_exclusive', 0)]:
            changed = copy.deepcopy(original)
            changed['regions']['exit_callee'][key] = value
            with patch.object(d.json, 'loads', return_value=changed):
                with self.assertRaises(ValueError):
                    d.audit_route()
