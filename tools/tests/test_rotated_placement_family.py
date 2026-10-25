import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_rotated_placement_family import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r155'

class RotatedPlacementFamilyTests(unittest.TestCase):
    def test_source_equivalence_and_each_original_image(self):
        r=analyze(EVIDENCE/'source',ROOT/'evidence/importer-loud-fail/r154/regression-rotated')
        self.assertEqual(json.loads(json.dumps(r)),json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['exact_images'],10)
        for v in r['images']:
            self.assertEqual(v['cpu']['exact'],240000)
            self.assertEqual(v['gpu']['exact'],240000)
        self.assertFalse(r['production_admitted'])
        self.assertFalse(r['full_production_suite_rerun'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
