import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.run_native_extent_rows import decode, compare
from tools.probes.run_native_color_order import compare as compare_order

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r62'


class NativeExtentRowsTests(unittest.TestCase):
    def test_original_order_stays_exact_with_actual_allocation(self):
        self.assertTrue(compare_order(EVIDENCE / 'order/order.json')['passed'])
        buffers = json.loads((EVIDENCE / 'order/buffers.json').read_text())
        self.assertEqual(len(buffers), 4)
        for row in buffers[:2]:
            self.assertEqual(row['size'], [70, 70])
            self.assertEqual(row['origin'], [37, 37])
            self.assertEqual(row['passes'], [[70, 70]] * 3)

    def test_extended_geometry_remains_rejected(self):
        native = decode(EVIDENCE / 'native')
        actual = json.loads((EVIDENCE / 'rows/rows.json').read_text())
        report = compare(native, actual)
        self.assertFalse(report['passed'])
        self.assertFalse(report['production_admitted'])
        for stage in ('input', 'filtered'):
            self.assertEqual(report['scores'][stage]['exact'], 6400)
        failures = report['scores']['final']['failures']
        self.assertEqual(report['scores']['final']['exact'], 6392)
        self.assertEqual({native[r['id']]['width'] for r in failures}, {17, 33})
        self.assertEqual(len(failures), 8)

    def test_missing_case_or_changed_extent_reject(self):
        native = decode(EVIDENCE / 'native')
        actual = json.loads((EVIDENCE / 'rows/rows.json').read_text())
        with self.assertRaises(ValueError):
            compare(native, actual[:-1])
        actual[0]['rect'][2] += 1
        with self.assertRaises(ValueError):
            compare(native, actual)

    def test_provenance_preserves_native_and_actual_buffers(self):
        for folder in ('order', 'rows'):
            p = EVIDENCE / folder
            provenance = json.loads((p / 'provenance.json').read_text())
            for key, root in [('source_sha256', ROOT), ('readback_sha256', p),
                              ('native_sha256', EVIDENCE / 'native')]:
                for name, digest in provenance.get(key, {}).items():
                    self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
