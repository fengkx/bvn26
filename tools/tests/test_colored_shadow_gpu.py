import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_colored_shadow_gpu import cases, compare

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r83/render'


class ColoredShadowGpuTests(unittest.TestCase):
    def test_nonwhite_gpu_retains_both_api_routes(self):
        rows = json.loads(gzip.decompress((EVIDENCE / 'rows.json.gz').read_bytes()))
        report = compare(cases(), rows)
        self.assertEqual(report, json.loads((EVIDENCE / 'comparison.json').read_text()))
        self.assertTrue(report['passed'])
        self.assertFalse(report['production_admitted'])
        for score in report['scores'].values():
            self.assertEqual(score, {'samples': 147456, 'exact': 147456, 'failures': []})
        rows[0]['input'][0][0] = 1
        self.assertFalse(compare(cases(), rows)['passed'])

    def test_inputs_and_gpu_implementation_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', ROOT), ('readback_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
        logs = list((EVIDENCE / 'batches').glob('*/godot.log'))
        self.assertEqual(len(logs), 24)
        for log in logs:
            self.assertNotIn('ERROR', log.read_text())
            self.assertIn('INTEGER_SHADOW_ROWS_OK cases=48 production_admitted=false', log.read_text())
