"""Preserve unknown joins and reject substituted evidence."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('s332', Path(__file__).with_name('diagnose.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class EvidenceTests(unittest.TestCase):
    def test_missing_live_bindings_cannot_qualify_controls(self):
        r = m.diagnose()
        self.assertFalse(r['production_admitted'])
        self.assertFalse(r['native_parity_proven'])
        self.assertTrue(all(v is None for v in r['observations'].values()))
        self.assertFalse(r['terminal_inventory_executed'])
        self.assertEqual(r['independently_observed_live_invocations'], [])
        self.assertFalse(r['off_on_controls_executed'])
        self.assertTrue(all(not g['proved'] for g in r['gates'].values()))
        self.assertTrue(all(v['qualified_witness'] is None for v in r['qualification_requirements'].values()))

    def test_changed_facility_rejected(self):
        original = Path.read_bytes
        def changed(path):
            value = original(path)
            return value+b'changed' if path.name == 'probe_owned_debugger.py' else value
        with patch.object(Path, 'read_bytes', changed), self.assertRaises(ValueError):
            m.diagnose()

    def test_changed_prior_rejected(self):
        original = Path.read_text
        def changed(path, *args, **kwargs):
            value = original(path, *args, **kwargs)
            return '{}' if path == m.HERE.parent/'s323/diagnosis.json' else value
        with patch.object(Path, 'read_text', changed), self.assertRaises(ValueError):
            m.diagnose()

    def test_all_cli_proof_flags_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            for gate in m.GATES:
                with self.subTest(gate=gate):
                    output = Path(tmp)/'report.json'
                    result = subprocess.run([sys.executable, str(m.HERE/'diagnose.py'),
                                             '--output', str(output), '--require-'+gate],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertIn('S332_'+gate.upper().replace('-', '_')+'_UNPROVED', result.stdout)
                    self.assertFalse(json.loads(output.read_text())['production_admitted'])
