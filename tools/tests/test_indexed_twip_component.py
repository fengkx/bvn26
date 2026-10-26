import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_indexed_twip_component import analyze
from tools.probes.indexed_twip_rect_candidate import render_leaf
from tools.probes.rect_mask_binding import canonical_rect_mask

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r153'

class IndexedTwipComponentTests(unittest.TestCase):
    def test_original_source_boundaries_and_coverage_rejection(self):
        r=analyze(ROOT/'evidence/importer-loud-fail/r142/fixture.json',ROOT/'evidence/importer-loud-fail/r141/native')
        self.assertEqual(json.loads(json.dumps(r)),json.loads((EVIDENCE/'summary.json').read_text()))
        for row in r['rows']:
            for key in ('cache','authored','pinned'):self.assertEqual(row[key]['exact'],240000)
        self.assertTrue(r['source_cpu_exact'])
        self.assertFalse(r['production_admitted'])
        self.assertFalse(r['gpu_binding_verified'])
        original=json.loads((ROOT/'evidence/importer-loud-fail/r142/fixture.json').read_text())
        leaf={**original['leaves']['8'],'indexed_storage_verified':True}
        leaf['fill_masks']=canonical_rect_mask(leaf)
        with self.assertRaises(AssertionError):render_leaf(leaf,{'sx':2,'sy':1,'tx':0,'ty':0},(1,1))
        with self.assertRaises(AssertionError):render_leaf(leaf,{'sx':1,'sy':1,'tx':0.125,'ty':0},(1,1))

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
