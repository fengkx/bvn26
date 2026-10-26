import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_jiraiya_source_cache import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r120'


class JiraiyaSourceCacheTests(unittest.TestCase):
    def test_source_cache_and_authored_blur_are_exact(self):
        result=analyze()
        self.assertEqual(result,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(len(result['comparisons']),6)
        for score in result['comparisons'].values():
            self.assertEqual(score['samples'],240000)
            self.assertEqual(score['exact'],240000)
            self.assertEqual(score['max_channel_delta'],[0,0,0,0])
        self.assertTrue(result['source_derived_cpu_component_exact'])
        self.assertFalse(result['gpu_binding_verified'])
        self.assertFalse(result['production_admitted'])

    def test_sources_and_native_references_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
