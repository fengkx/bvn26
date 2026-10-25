import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_jiraiya_pinned_composite import compare

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r123'


class JiraiyaLiveCacheTests(unittest.TestCase):
    def test_final_rgb_matches_both_original_component_images(self):
        result=compare(EVIDENCE/'gpu')
        stored=json.loads((EVIDENCE/'summary.json').read_text())
        self.assertTrue(stored.pop('live_viewport_texture_verified'))
        self.assertEqual(result,stored)
        self.assertEqual(result['exact_images'],2)
        self.assertEqual(sum(v['exact'] for v in result['images']),480000)
        self.assertFalse(result['production_admitted'])
        self.assertFalse(result['full_production_suite_rerun'])

    def test_composition_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'gpu/provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('readback_sha256',EVIDENCE/'gpu')]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
        self.assertEqual(p['exit'],0)
