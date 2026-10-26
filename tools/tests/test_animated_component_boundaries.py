import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_animated_component_boundaries import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r141'


class AnimatedComponentBoundaryTests(unittest.TestCase):
    def test_original_clocks_and_restored_filter_boundaries(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(len(r['clocks']),24)
        self.assertEqual([v['tick'] for v in r['rows']],[0,4,8,11])
        for v in r['rows']:
            for name in ('cache_vs_clear','cache_to_authored','pinned'):
                self.assertEqual(v[name]['exact'],240000)
        self.assertFalse(r['source_derived_input_verified'])
        self.assertFalse(r['production_admitted'])

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
