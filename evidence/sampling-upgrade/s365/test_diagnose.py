"""Reject byte drift, forged semantics and loss of complete retained evidence."""
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
spec = importlib.util.spec_from_file_location('s365', HERE / 'diagnose.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = m.replay()
        cls.native = json.loads((HERE / 'native-prefix.json').read_text())
        cls.saved = json.loads((HERE / 'saved-reference-attempt.json').read_text())

    def test_actual_prefix_and_unproved_frontiers(self):
        report = m.diagnose()
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['native_parity_proven'])
        self.assertEqual(report['m0_02_status'], 'pending')
        self.assertEqual(report['audit']['taken_target'], 0x10005d9b4)
        self.assertEqual(report['audit']['fallthrough'], 0x10005d96b)
        self.assertEqual(report['audit']['condition'], 'incoming RDI == 0')
        self.assertTrue(all(not g['proved'] for g in report['gates'].values()))
        self.assertTrue(all(v is None for v in report['observations'].values()))
        self.assertEqual(set(report['lookup_paths']), {'parent_depth', 'saved_reference'})

    def test_every_rehashed_byte_mutation_rejected(self):
        for index in range(len(m.PREFIX)):
            record = copy.deepcopy(self.native)
            data = bytearray(m.PREFIX)
            data[index] ^= 1
            record.update(hex=data.hex(), sha256=m.sha(data))
            with self.subTest(index=index), self.assertRaises(ValueError):
                m.audit(record, self.prior)

    def test_metadata_and_semantic_promotion_rejected(self):
        for key in self.native:
            record = copy.deepcopy(self.native)
            record[key] = 'changed'
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.audit(record, self.prior)
        record = dict(self.native, parent_resolver=True)
        with self.assertRaises(ValueError):
            m.audit(record, self.prior)

    def test_saved_representation_cannot_be_borrowed(self):
        for key in self.saved:
            record = copy.deepcopy(self.saved)
            record[key] = not record[key] if isinstance(record[key], bool) else True
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.audit_saved(record)

    def test_complete_prior_not_subset(self):
        prior = copy.deepcopy(self.prior)
        prior['observations']['invented'] = 'proof'
        with self.assertRaises(ValueError):
            m.audit(self.native, prior)
        with patch.object(m, 'load') as loader:
            loader.return_value.diagnose.return_value = prior
            with self.assertRaises(ValueError):
                m.replay()

    def test_pin_drift_rejected(self):
        original = Path.read_bytes
        for target in ('native-prefix.json', 'resolve_relative.py', 'next-fix-priority-after-s362.md'):
            def changed(path):
                value = original(path)
                return value + b'changed' if path.name == target else value
            with self.subTest(target=target), patch.object(Path, 'read_bytes', changed), self.assertRaises(ValueError):
                m.diagnose()

    def test_wrong_binary_rejected(self):
        extractor = m.load('s365_extract_test', HERE / 'extract_native.py')
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / 'wrong-player'
            binary.write_bytes(b'not the receipt-matching player')
            with self.assertRaises(ValueError):
                extractor.extract(binary)

    def test_base_and_proof_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            for flags in ([], *[['--require-' + g] for g in m.GATES], ['--require-' + g for g in m.GATES]):
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output',
                                         str(Path(tmp) / 'report.json'), *flags], capture_output=True, text=True)
                with self.subTest(flags=flags):
                    self.assertEqual(result.returncode, int(bool(flags)), result.stderr)
                    self.assertNotIn('EVIDENCE_INVALID', result.stderr)
                    for flag in flags:
                        self.assertIn('S365_' + flag.removeprefix('--require-').upper().replace('-', '_') + '_UNPROVED', result.stdout)


if __name__ == '__main__':
    unittest.main()
