import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.run_affine_nearest_integer import compare,fixture
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r178/gpu'

class AffineNearestIntegerTests(unittest.TestCase):
    def test_gpu_readbacks_match_pinned_native_without_tolerance(self):
        r=compare(EVIDENCE)
        self.assertEqual(r,json.loads((EVIDENCE/'report.json').read_text()))
        self.assertEqual(r['exact'],68322)
        self.assertTrue(r['bounded_gpu_exact'])
        self.assertFalse(r['production_admitted'])

    def test_metadata_regeneration_and_complete_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key in ('source_sha256','reference_sha256'):
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);spec=fixture(out)
            self.assertLess(spec['max_integer_intermediate'],2**31)
            for name,digest in p['readback_sha256'].items():
                path=out/name if (out/name).exists() else EVIDENCE/name
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
