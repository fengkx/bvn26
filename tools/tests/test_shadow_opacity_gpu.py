import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_shadow_opacity_gpu import cases, compare

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r85'


class ShadowOpacityGpuTests(unittest.TestCase):
    def test_materialized_gpu_is_exact_and_stale_copy_is_rejected(self):
        expected = cases()
        for order in ('fresh', 'stale'):
            folder = EVIDENCE / order
            rows = json.loads(gzip.decompress((folder / 'rows.json.gz').read_bytes()))
            r = compare(expected, rows, order)
            self.assertEqual(r, json.loads(gzip.decompress((folder / 'comparison.json.gz').read_bytes())))
            self.assertEqual(r['passed'], order == 'fresh')
            self.assertFalse(r['production_admitted'])
            for stage, score in r['scores'].items():
                self.assertEqual(score['samples'], 46080)
                self.assertEqual(score['exact'], 0 if order == 'stale' and stage in ('parent', 'final') else 46080)
            rows[0]['sizes'][0][0] = 65
            with self.assertRaisesRegex(ValueError, 'Allocation'):
                compare(expected, rows, order)

    def test_actual_node_inputs_and_gpu_bytes_are_pinned(self):
        for order in ('fresh', 'stale'):
            folder = EVIDENCE / order
            p = json.loads((folder / 'provenance.json').read_text())
            for key, root in [('source_sha256', ROOT), ('native_sha256', ROOT), ('readback_sha256', folder)]:
                for name, digest in p[key].items():
                    self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
            logs = list((folder / 'batches').glob('*/godot.log'))
            self.assertEqual(len(logs), 15)
            for log in logs:
                self.assertNotIn('ERROR', log.read_text())
                self.assertIn(f'SHADOW_OPACITY_ROWS_OK cases=24 order={order} production_admitted=false', log.read_text())
