import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_jiraiya_source_cache_gpu import compare_readbacks
from tools.probes.analyze_jiraiya_cache_boundary import decode

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r121'


class JiraiyaSourceCacheGpuTests(unittest.TestCase):
    def test_actual_gpu_buffers_match_original_native_images(self):
        report=json.loads((EVIDENCE/'gpu/report.json').read_text())
        native,_,_=decode(ROOT/'evidence/importer-loud-fail/r100/native')
        scores=compare_readbacks(EVIDENCE/'gpu',report['metadata'],native)
        self.assertEqual(scores,report['comparisons'])
        for score in scores.values():
            self.assertEqual(score['exact'],score['samples'])
            self.assertEqual(score['max_channel_delta'],[0,0,0,0])
        allocations=json.loads((EVIDENCE/'gpu/allocations.json').read_text())
        self.assertEqual(allocations,[{'size':[117,74],'padding':[21,0],'axes':[0,0,0]}]*3)
        self.assertTrue(report['diagnostic_passed'])
        self.assertFalse(report['production_admitted'])

    def test_gpu_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'gpu/provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('native_sha256',ROOT),('readback_sha256',EVIDENCE/'gpu')]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
        self.assertTrue(all(c['exit']==0 for c in p['commands']))
