import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_jiraiya_bitmap_binding import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r89'


class JiraiyaBitmapBindingTests(unittest.TestCase):
    def test_real_fill_translation_requires_separate_stage_and_retains_counterexamples(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertFalse(r['whole_image_admitted'])
        self.assertFalse(r['production_admitted'])
        self.assertEqual(r['scores']['compose_before_quantization']['exact_images'],0)
        separate=r['scores']['inverse_draw_then_fill']
        self.assertEqual(separate['exact_images'],5)
        self.assertEqual([(c['case'],len(c['failures'])) for c in separate['cases'] if c['failures']],[(3,3)])
        self.assertEqual([(p['x'],p['y']) for p in separate['cases'][3]['failures']],[(75,20),(75,26),(75,27)])
        for c in separate['cases']:
            self.assertEqual(c['regions']['fringe']['native_nonzero_alpha'],0)

    def test_original_tags_and_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
