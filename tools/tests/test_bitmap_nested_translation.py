import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_nested_translation import analyze,source_leaf_heldout

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r95'


class BitmapNestedTranslationTests(unittest.TestCase):
    def test_independent_matrix_controls_and_heldout_source(self):
        r=analyze(EVIDENCE/'native');r['source_leaf_heldout']=source_leaf_heldout()
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(r['scores']['direct']['composed_double']['exact'],26538)
        self.assertEqual(r['scores']['nested']['separate_quarters']['exact'],26538)
        self.assertEqual(r['scores']['nested']['inner_quarter_only']['exact'],26538)
        self.assertEqual(r['scores']['nested']['composed_double']['exact'],21819)
        self.assertEqual(r['source_leaf_heldout']['comparison']['exact'],240000)
        self.assertFalse(r['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
