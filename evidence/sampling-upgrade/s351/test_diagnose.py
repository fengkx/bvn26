"""Reject false reference associations and keep unobserved controls closed."""
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
spec = importlib.util.spec_from_file_location('s351', HERE / 'diagnose.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
r = m.load('s351_resolver', HERE / 'resolve_references.py')


class EvidenceTests(unittest.TestCase):
    def test_diagnosis_keeps_paths_separate(self):
        report = m.diagnose()
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['native_parity_proven'])
        self.assertEqual(report['m0_02_status'], 'pending')
        self.assertEqual(set(report['lookup_paths']), {'parent_depth', 'saved_reference'})
        self.assertTrue(all(not p['derived'] for p in report['lookup_paths'].values()))
        self.assertTrue(all(v is None for v in report['observations'].values()))
        self.assertFalse(report['saved_reference_attempt']['slot_result_borrowed'])

    def test_absolute_reference_scans_unaligned_bytes(self):
        import struct
        pointer = struct.pack('<Q', 0x10119efe1)
        self.assertEqual(r.references(b'x' + pointer + b'xy' + pointer, 0x10119efe1), [1, 11])
        self.assertEqual(r.references(pointer, 0x10119efe2), [])

    def test_wrong_player_rejected(self):
        with self.assertRaises(ValueError):
            r.extract(b'not the receipt-pinned player')

    def test_no_static_to_live_promotion(self):
        original = json.loads((HERE / 'reference-attempt.json').read_text())
        for key in ('executable_association', 'saved_reference_dereference', 'live_generations', 'controls_executed'):
            record = copy.deepcopy(original)
            record[key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
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
            return value + b'changed' if path.name == 'reference-attempt.json' else value
        with patch.object(Path, 'read_bytes', changed), self.assertRaises(ValueError):
            m.diagnose()

    def test_every_proof_flag_fails_honestly(self):
        with tempfile.TemporaryDirectory() as tmp:
            for gate in m.GATES:
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output', str(Path(tmp) / 'report.json'), '--require-' + gate], capture_output=True, text=True)
                with self.subTest(gate=gate):
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertIn('S351_' + gate.upper().replace('-', '_') + '_UNPROVED', result.stdout)
