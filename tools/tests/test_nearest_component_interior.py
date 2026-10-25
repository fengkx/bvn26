import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.run_nearest_component_interior import compare,fixture
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r180/gpu'

class NearestComponentInteriorTests(unittest.TestCase):
    def test_gpu_interior_exact_without_admitting_edges(self):
        r=compare(EVIDENCE)
        self.assertEqual(r,json.loads((EVIDENCE/'report.json').read_text()))
        self.assertEqual(sum(v['exact'] for v in r['rows']),52921)
        self.assertEqual([v['unproven_nonzero_native_pixels'] for v in r['rows']],[3,12])
        self.assertFalse(r['complete_component_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_original_metadata_regenerates_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for name,digest in p['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);fixture(out)
            for name,digest in p['readback_sha256'].items():
                path=out/name if (out/name).exists() else EVIDENCE/name
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
