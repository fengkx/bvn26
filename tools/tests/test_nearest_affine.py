import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_nearest_affine import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r158'

class NearestAffineTests(unittest.TestCase):
    def test_native_inputs_and_rejected_common_initializers(self):
        r=analyze(EVIDENCE/'native');f={k:v.pop('failures') for k,v in r['scores'].items()}
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(f,json.loads(gzip.decompress((EVIDENCE/'failures.json.gz').read_bytes())))
        self.assertEqual(r['source_texels_exact'],256)
        self.assertEqual(r['scores']['fixed_inverse_center']['exact'],18251)
        self.assertEqual(r['scores']['fixed_inverse_center']['samples'],22261)
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
