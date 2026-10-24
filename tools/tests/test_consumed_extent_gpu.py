import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_integer_extent_gpu import cases, compare
from tools.probes.analyze_blur_kernel_consumption import consume

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r74/render'


class ConsumedExtentGpuTests(unittest.TestCase):
    def test_integer_blur_clears_all_pinned_native_stages(self):
        rows = json.loads(gzip.decompress((EVIDENCE / 'rows.json.gz').read_bytes()))
        expected = cases()
        report = compare(expected, rows)
        self.assertTrue(report['passed'])
        self.assertFalse(report['production_admitted'])
        for score in report['scores'].values():
            self.assertEqual((score['exact'], score['pixels'], score['failures']), (115840, 115840, []))
        for row, case in zip(rows, expected):
            operands = [] if case['kernel'] <= 1 else [
                {'kernel': consume(case['kernel'], 'six_significant_bits'), 'direction': direction}
                for direction in ([1, 0], [0, 1])]
            self.assertEqual(row['blur_operands'], operands)

    def test_sources_native_readbacks_and_clean_batches_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', ROOT), ('readback_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
        logs = list((EVIDENCE / 'batches').glob('*/godot.log'))
        self.assertEqual(len(logs), 12)
        for log in logs:
            self.assertNotIn('ERROR', log.read_text())
            self.assertIn('CONSUMED_EXTENT_ROWS_OK', log.read_text())
