import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.analyze_jiraiya_first_draw import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r94'


class JiraiyaFirstDrawTests(unittest.TestCase):
    def test_independent_instances_reject_draw_order_explanation(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=analyze(EVIDENCE/'native',Path(tmp))
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(len(r['comparisons']),7)
        self.assertTrue(all(s['exact']==s['samples']==240000 for s in r['comparisons'].values()))
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
