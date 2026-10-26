import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_indexed_component_live import compare,fixture
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r154/gpu'

class IndexedComponentLiveTests(unittest.TestCase):
    def test_live_buffers_and_original_complete_images(self):
        r=compare(EVIDENCE)
        self.assertEqual(json.loads(json.dumps(r)),json.loads((EVIDENCE/'report.json').read_text()))
        self.assertEqual(r['exact_images'],4)
        self.assertTrue(r['live_indexed_component_exact'])
        self.assertFalse(r['production_admitted'])
        self.assertFalse(r['full_production_suite_rerun'])
        self.assertEqual(fixture(),json.loads((EVIDENCE/'fixture.json').read_text()))

    def test_source_and_gpu_readback_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('readback_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
