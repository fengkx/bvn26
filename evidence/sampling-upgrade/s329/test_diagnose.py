import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('s329', Path(__file__).with_name('diagnose.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class EvidenceTests(unittest.TestCase):
    def test_no_binding_promoted(self):
        report = m.diagnose()
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['native_parity_proven'])
        for row in report['bindings']:
            self.assertTrue(all(v is None for k, v in row.items() if k != 'boundary'))
        self.assertTrue(all(not g['proved'] for g in report['gates'].values()))

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
            return '{}' if path == m.HERE.parent/'s318/diagnosis.json' else value
        with patch.object(Path, 'read_text', changed), self.assertRaises(ValueError):
            m.diagnose()
