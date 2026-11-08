"""Protect custody and reject static-address promotion to native identity."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s360', HERE / 'diagnose.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
r = m.load('s360_relative', HERE / 'resolve_relative.py')


class EvidenceTests(unittest.TestCase):
    def test_diagnosis_keeps_paths_separate(self):
        report = m.diagnose()
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['native_parity_proven'])
        self.assertEqual(report['m0_02_status'], 'pending')
        self.assertTrue(report['gates']['relative-code-association']['proved'])
        self.assertEqual(set(report['lookup_paths']), {'parent_depth', 'saved_reference'})
        self.assertTrue(all(not p['derived'] for p in report['lookup_paths'].values()))
        self.assertTrue(all(v is None for v in report['observations'].values()))
        self.assertFalse(report['saved_reference_attempt']['slot_result_borrowed'])

    def test_signed_displacements_and_section_mapping(self):
        for displacement in (-100, 100):
            code = b'\x48\x8d\x35' + struct.pack('<i', displacement)
            raw = b'xx' + code + b'yy'
            target = 0x1000 + 7 + displacement
            result = r.relative_candidates(raw, 2, 0x1000, 7, (target,))
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['file_offset'], 2)
            self.assertEqual(result[0]['target'], target)
            self.assertEqual(r.relative_candidates(raw, 2, 0x1000, 6, (target,)), [])

    def test_non_rip_modrm_rejected(self):
        code = b'\x48\x8d\x34' + struct.pack('<i', 10)
        self.assertEqual(r.relative_candidates(code, 0, 100, 7, (117,)), [])

    def test_function_start_uleb_and_truncation(self):
        self.assertEqual(r.function_starts(b'\x80\x01\x10\x00', 0x1000), [0x1080, 0x1090])
        for stream in (b'\x80', b'\x01'):
            with self.assertRaises(ValueError):
                r.function_starts(stream, 0)

    def test_wrong_player_rejected(self):
        with self.assertRaises(ValueError):
            r.extract(b'not the receipt-pinned player')

    def test_no_static_to_live_promotion(self):
        original = json.loads((HERE / 'relative-attempt.json').read_text())
        for key in ('parent_depth_resolver', 'saved_reference_dereference', 'live_generations', 'controls_executed'):
            record = copy.deepcopy(original)
            record[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.audit_attempt(record)

    def test_changed_relative_arithmetic_rejected(self):
        record = json.loads((HERE / 'relative-attempt.json').read_text())
        record['relative_code_association']['signed_displacement'] += 1
        with self.assertRaises(ValueError):
            m.audit_attempt(record)

    def test_changed_prior_rejected(self):
        original = Path.read_bytes
        def changed(path):
            value = original(path)
            return value + b'changed' if path.name == 'probe_owned_debugger.py' else value
        with patch.object(Path, 'read_bytes', changed), self.assertRaises(ValueError):
            m.diagnose()

    def test_changed_route_rejected(self):
        original = Path.read_bytes
        def changed(path):
            value = original(path)
            return value + b'changed' if path.name == 'relative-attempt.json' else value
        with patch.object(Path, 'read_bytes', changed), self.assertRaises(ValueError):
            m.diagnose()

    def test_gate_exits_distinguish_static_and_native_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            for gate in m.GATES:
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output', str(Path(tmp) / 'report.json'), '--require-' + gate], capture_output=True, text=True)
                with self.subTest(gate=gate):
                    self.assertEqual(result.returncode, 0 if gate == 'relative-code-association' else 1, result.stderr)
                    if gate != 'relative-code-association':
                        self.assertIn('S360_' + gate.upper().replace('-', '_') + '_UNPROVED', result.stdout)


if __name__ == '__main__':
    unittest.main()
