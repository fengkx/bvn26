import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.analyze_jiraiya_cache_boundary import analyze,SHIFTS

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r100'


class JiraiyaCacheBoundaryTests(unittest.TestCase):
    def test_actual_cache_images_explain_filter_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=analyze(EVIDENCE/'native',Path(tmp))
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        for offset in SHIFTS:
            for suffix in ('authored-pinned','clear-pinned','zero-vs-cache','restored-vs-authored','cache-shifted','zero-shifted','blur-cache-vs-authored','blur-zero-vs-authored'):
                self.assertEqual(r['comparisons'][f'{offset}-{suffix}']['exact'],240000)
        self.assertEqual(r['comparisons']['0-cache-vs-clear']['exact'],239731)
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
