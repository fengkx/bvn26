import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.probes.analyze_jiraiya_buffer_origin import analyze,SHIFTS

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r99'


class JiraiyaBufferOriginTests(unittest.TestCase):
    def test_independent_integer_translations(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=analyze(EVIDENCE/'native',Path(tmp))
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        for offset in SHIFTS:
            self.assertEqual(r['comparisons'][f'{offset}-authored-aligned']['exact'],240000)
            self.assertEqual(r['comparisons'][f'{offset}-input-model']['exact'],240000)
        self.assertEqual(r['comparisons']['-128-input-aligned']['exact'],239957)
        self.assertEqual(r['comparisons']['128-input-aligned']['exact'],239944)
        self.assertFalse(r['production_admitted'])

    def test_nontransparent_fractional_coverage_rejects(self):
        from tools.probes.analyze_jiraiya_bitmap_binding import decode
        from tools.probes.bound_bitmap_candidate import render_leaf
        fixture,_=decode(ROOT/'evidence/importer-loud-fail/r89/native')
        fixture['pixels_premultiplied'][0]=[1,1,1,1]
        with self.assertRaisesRegex(AssertionError,'Unproven fractional coverage'):
            render_leaf(fixture,fixture['cases'][0],fixture['target_size'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
