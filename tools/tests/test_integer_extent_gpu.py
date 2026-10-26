import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_integer_extent_gpu import cases, compare

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r70/render'


class IntegerExtentGpuTests(unittest.TestCase):
    def test_actual_allocation_exposes_near_integer_filter_failures(self):
        rows = json.loads(gzip.decompress((EVIDENCE / 'rows.json.gz').read_bytes()))
        r = compare(cases(), rows)
        self.assertFalse(r['passed'])
        self.assertFalse(r['production_admitted'])
        self.assertEqual(r['scores']['input']['exact'], 115840)
        self.assertEqual(r['scores']['filtered']['exact'], 115596)
        self.assertEqual(r['scores']['final']['exact'], 115678)
        for stage in ('filtered', 'final'):
            self.assertEqual({v['kernel'] for v in r['scores'][stage]['failures']}, {3.99609375, 7.99609375})
            self.assertEqual({v['source'] for v in r['scores'][stage]['failures']}, {'r68'})

    def test_sources_native_readbacks_and_clean_batches_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', ROOT), ('readback_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
        logs = list((EVIDENCE / 'batches').glob('*/godot.log'))
        self.assertEqual(len(logs), 12)
        for log in logs:
            self.assertNotIn('ERROR', log.read_text())
            self.assertIn('INTEGER_EXTENT_ROWS_OK', log.read_text())
