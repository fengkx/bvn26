import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_yulong_rotated_live import compare,fixture

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r140/gpu'


class YulongRotatedLiveTests(unittest.TestCase):
    def test_original_pinned_images_and_actual_buffer_boundaries(self):
        r=compare(EVIDENCE)
        self.assertEqual(r,json.loads((EVIDENCE/'report.json').read_text()))
        self.assertEqual(fixture(),json.loads((EVIDENCE/'fixture.json').read_text()))
        self.assertEqual(r['exact_images'],2)
        self.assertTrue(r['live_rotated_glow_diagnostic_exact'])
        self.assertFalse(r['production_admitted'])
        self.assertFalse(r['full_production_suite_rerun'])

    def test_gpu_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('readback_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
