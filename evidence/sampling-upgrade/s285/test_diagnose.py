"""Negative controls for the bounded s285 evidence audit."""
import gzip
import importlib.util
import json
import struct
import tarfile
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s285_diagnosis', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class NestedLifetimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.diagnose()
        cls.lines = gzip.decompress((HERE.parent / 's275/native-capture.log.gz').read_bytes()).decode().splitlines()
        cls.raw = (audit.ROOT / 'game/fighter/yulong.swf').read_bytes()

    def test_replay_preserves_unknowns(self):
        self.assertEqual(self.report['retained_events_revalidated'], 5214)
        self.assertEqual(self.report['actor_rows_equal_s247'], 122)
        for key in ('production_admitted', 'native_parity_proven', 'runtime_binding_proved',
                    'parent_removal_dispatch_proved', 'direct_nested_invocation_proved',
                    'observer_perturbation_qualified'):
            self.assertFalse(self.report[key])
        self.assertIsNone(self.report['nested_function_audit']['direct_invocation_observed'])
        self.assertEqual(self.report['observer_qualification']['timing_control_pairs'], 0)

    def test_source_removal_bytes(self):
        rows = audit.removal_tags(self.raw)
        self.assertEqual([(r['sprite'], r['frame'], r['depth'], r['tag_hex']) for r in rows],
                         [(104, 5, 2, '02070200'), (345, 194, 28, '02071c00')])

    def test_wrong_parent_depth_rejected(self):
        rows = audit.removal_tags(self.raw)
        data = bytearray(self.raw[:8] + zlib.decompress(self.raw[8:]))
        data[:3] = b'FWS'
        struct.pack_into('<H', data, rows[1]['uncompressed_offset'] + 2, 27)
        with self.assertRaisesRegex(ValueError, 'changed removal depth'):
            audit.removal_tags(bytes(data))

    def test_missing_parent_tag_rejected(self):
        rows = audit.removal_tags(self.raw)
        data = bytearray(self.raw[:8] + zlib.decompress(self.raw[8:]))
        data[:3] = b'FWS'
        struct.pack_into('<H', data, rows[1]['uncompressed_offset'], (9 << 6) | 2)
        with self.assertRaisesRegex(ValueError, 'missing selected removal'):
            audit.removal_tags(bytes(data))

    def test_missing_body_state_cannot_join_slots(self):
        lines = [line for line in self.lines if not ('|21|state|p1,' in line)]
        with self.assertRaisesRegex(ValueError, 'state/slot join'):
            audit.correlate(lines)

    def test_rename_cannot_substitute_for_removal(self):
        lines = [line.replace('|21|state|p1,193,', '|21|state|p1,194,') for line in self.lines]
        with self.assertRaisesRegex(ValueError, 'parent removal bracket'):
            audit.correlate(lines)

    def test_missing_operand_record_rejected(self):
        lines = [line for line in self.lines if not ('|18|s275_value|receiver4,' in line)]
        with self.assertRaisesRegex(ValueError, 'operand evaluation'):
            audit.correlate(lines)

    def test_function_mutation_or_extra_call_not_initialization(self):
        source = next(s['source'] for s in json.loads((audit.ROOT / 'scripts/fighter/yulong.json').read_text())['scripts'] if s['path'] == audit.NESTED)
        with tarfile.open(HERE.parent / 's275/native-build.tar.gz') as archive:
            archived = archive.extractfile('patches/fighter/yulong/' + audit.NESTED).read().decode()
        with self.assertRaisesRegex(ValueError, 'bodies differ'):
            audit.nested_audit(source, archived.replace('_parent.pn', '_parent._parent.pn', 1))
        with self.assertRaisesRegex(ValueError, 'unclassified'):
            audit.nested_audit(source, archived + '\nthis.checkHit();\n')


if __name__ == '__main__':
    unittest.main()
