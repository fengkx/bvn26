import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.run_packed_matrix_rows import specimens, fixture, compare
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r207/gpu'

class PackedMatrixRowsTests(unittest.TestCase):
    def test_recorded_gpu_against_pinned_native_and_regenerated_inputs(self):
        rows=specimens()
        proof=json.loads((EVIDENCE/'provenance.json').read_text())
        with tempfile.TemporaryDirectory(prefix='matrix-gpu-') as directory:
            output=Path(directory)
            spec=fixture(output,rows)
            for path in output.iterdir():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),proof['artifact_sha256'][path.name])
        result=compare(EVIDENCE,spec,rows)
        self.assertEqual(result,json.loads((EVIDENCE/'report.json').read_text()))
        self.assertEqual(sum(r['samples'] for r in result['comparisons'].values()),401784)
        self.assertTrue(result['exact'])
        self.assertFalse(result['production_admitted'])

    def test_source_and_readback_provenance(self):
        proof=json.loads((EVIDENCE/'provenance.json').read_text())
        for name,digest in proof['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)
        for path in EVIDENCE.iterdir():
            if path.name!='provenance.json':self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),proof['artifact_sha256'][path.name])
