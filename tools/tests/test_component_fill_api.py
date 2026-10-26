import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_component_fill_api import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r144'


class ComponentFillAPITests(unittest.TestCase):
    def test_same_bytes_and_properties_do_not_imply_api_equivalence(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(json.loads(json.dumps(r)),json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['source_pixels_exact'],2275)
        self.assertEqual(r['api_comparisons']['cache']['exact'],239338)
        self.assertEqual(r['unchanged_cpu_cache']['as']['exact'],240000)
        self.assertEqual(r['unchanged_cpu_cache']['tag']['exact'],239338)
        for v in r['prior_tag_reference'].values():self.assertEqual(v['exact'],240000)
        self.assertFalse(r['api_equivalence_verified'])
        self.assertFalse(r['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
