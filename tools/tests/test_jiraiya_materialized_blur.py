import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.analyze_jiraiya_materialized_blur import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r98'


class JiraiyaMaterializedBlurTests(unittest.TestCase):
    def test_explicit_native_materialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=analyze(EVIDENCE/'native',Path(tmp))
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        for name in ('authored_vs_pinned','input_vs_pinned','materialized_input','input_not_mutated','integer_vs_apply','integer_vs_bitmap-filter'):
            self.assertEqual(r['comparisons'][name]['exact'],240000,name)
        for name in ('integer_vs_authored','apply_vs_authored','bitmap_filter_vs_authored'):
            self.assertEqual(r['comparisons'][name]['exact'],239723,name)
            self.assertEqual(r['comparisons'][name]['max_channel_delta'],[1,1,1,1])
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
