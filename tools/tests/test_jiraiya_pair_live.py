import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_jiraiya_pair_live import compare

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r127'


class JiraiyaPairLiveTests(unittest.TestCase):
    def test_both_components_share_exact_live_gpu_path(self):
        result=compare(EVIDENCE/'gpu')
        self.assertEqual(result,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(result['exact_images'],4)
        self.assertEqual(sum(v['exact'] for v in result['images']),960000)
        self.assertTrue(result['shared_live_gpu_path_verified'])
        self.assertFalse(result['production_admitted'])
        self.assertFalse(result['full_production_suite_rerun'])

    def test_gpu_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'gpu/provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('readback_sha256',EVIDENCE/'gpu')]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
        self.assertTrue(all(c['exit']==0 for c in p['commands']))
