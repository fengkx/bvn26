import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.run_packed_matrix_family import fixture
from tools.probes.run_nearest_matrix_family import compare
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r208/gpu'
NATIVE=ROOT/'evidence/importer-loud-fail/r195/native'

class PackedMatrixFamilyTests(unittest.TestCase):
    def test_complete_live_family_and_boundaries_are_native_exact(self):
        result=compare(EVIDENCE,NATIVE)
        self.assertEqual(result,json.loads((EVIDENCE/'report.json').read_text()))
        self.assertEqual(result['exact_images'],12)
        self.assertTrue(result['full_family_exact'])
        self.assertEqual(sum(r['samples'] for r in result['rgba_boundaries']),979416)
        self.assertFalse(result['production_admitted'])

    def test_original_metadata_regenerates_and_provenance_is_pinned(self):
        proof=json.loads((EVIDENCE/'provenance.json').read_text())
        for name,digest in proof['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)
        with tempfile.TemporaryDirectory(prefix='packed-family-') as directory:
            out=Path(directory);fixture(out,NATIVE)
            for name,digest in proof['readback_sha256'].items():
                path=out/name if (out/name).exists() else EVIDENCE/name
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
