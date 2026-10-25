import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.run_nearest_matrix_component import compare,fixture
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r194/gpu'

class NearestMatrixComponentTests(unittest.TestCase):
    def test_live_actual_filter_and_final_images(self):
        r=compare(EVIDENCE)
        self.assertEqual(r,json.loads((EVIDENCE/'report.json').read_text()))
        self.assertEqual(r['exact_images'],4)
        self.assertTrue(r['live_final_wrapper_exact'])
        self.assertEqual(sum(v['exact_alpha'] for v in r['alpha_boundaries']),326472)
        self.assertFalse(r['matrix_rgb_intermediate_proved'])
        self.assertFalse(r['production_admitted'])

    def test_original_metadata_regenerates_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for name,digest in p['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);fixture(out)
            for name,digest in p['readback_sha256'].items():
                path=out/name if (out/name).exists() else EVIDENCE/name
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
