import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_grouped_blur_gpu import cases, compare

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r75/render'


class GroupedBlurGpuTests(unittest.TestCase):
    def test_actual_pass_chain_and_native_samples_are_exact(self):
        rows = json.loads(gzip.decompress((EVIDENCE / 'rows.json.gz').read_bytes()))
        report = compare(cases(), rows)
        self.assertTrue(report['passed'])
        self.assertFalse(report['production_admitted'])
        for score in report['scores'].values():
            self.assertEqual((score['exact'], score['samples'], score['failures']), (165888, 165888, []))
        rows[0]['size'][0] += 1
        with self.assertRaisesRegex(ValueError, 'allocation/order/operands'):
            compare(cases(), rows)

    def test_sources_native_readbacks_and_clean_batches_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', ROOT), ('readback_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
        logs = list((EVIDENCE / 'batches').glob('*/godot.log'))
        self.assertEqual(len(logs), 27)
        for log in logs:
            self.assertNotIn('ERROR', log.read_text())
            self.assertIn('GROUPED_BLUR_ROWS_OK cases=48 production_admitted=false', log.read_text())
