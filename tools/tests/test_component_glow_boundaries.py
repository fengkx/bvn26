import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_component_glow_boundaries import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r131'


class ComponentGlowBoundariesTests(unittest.TestCase):
    def test_native_cache_explains_original_glow(self):
        result=analyze(EVIDENCE/'native')
        self.assertEqual(result,json.loads((EVIDENCE/'summary.json').read_text()))
        for i,exact in enumerate((240000,240000,240000)):
            self.assertEqual(result['comparisons'][f'{i}-cache-vs-clear']['exact'],exact)
            self.assertEqual(result['comparisons'][f'{i}-glow-cache-vs-authored']['exact'],240000)
        self.assertEqual(sum(v['exact'] for v in result['pinned_comparisons']),480000)
        self.assertFalse(result['source_derived_input_verified'])
        self.assertFalse(result['production_admitted'])

    def test_sources_and_native_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
