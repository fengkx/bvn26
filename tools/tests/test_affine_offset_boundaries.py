import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_offset_boundaries import analyze
from tools.probes.generate_affine_offset_boundaries import generate,select
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r175'
OLD=ROOT/'evidence/importer-loud-fail/r171/native'

class AffineOffsetBoundariesTests(unittest.TestCase):
    def test_native_discriminates_offset_rounding(self):
        r=analyze(EVIDENCE/'native',OLD);f={k:v.pop('failures') for k,v in r['scores'].items()}
        self.assertEqual(f,json.loads(gzip.decompress((EVIDENCE/'failures.json.gz').read_bytes())))
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['scores']['round_offset']['exact'],45)
        self.assertEqual(r['scores']['exact_norm']['centers_exact'],0)
        self.assertFalse(r['production_admitted'])

    def test_probe_regenerates_from_transform_properties(self):
        self.assertEqual(generate(select(OLD)),(ROOT/'tools/probes/flash_filters/bitmap-affine-offset-boundaries.as').read_text())

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
