import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.analyze_jiraiya_filter_boundary import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r93'


class JiraiyaFilterBoundaryTests(unittest.TestCase):
    def test_explicit_boundary_observations(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=analyze(EVIDENCE/'native',Path(tmp))
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        scores=r['comparisons']
        for name in ('authored_vs_pinned','reassigned_vs_authored','child_draw_vs_r92_leaf','next_frame_vs_cleared'):
            self.assertEqual(scores[name]['exact'],240000,name)
        self.assertEqual(scores['cleared_vs_authored']['exact'],235024)
        self.assertEqual(scores['cleared_vs_child_draw']['exact'],238233)
        self.assertEqual([p[5] for p in r['properties']],['1','0','1','0'])
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
