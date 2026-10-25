import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_affine_scale_split import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r167'

class AffineScaleSplitTests(unittest.TestCase):
    def test_complete_zero_phase_images_before_amplification(self):
        r=analyze(EVIDENCE/'native',ROOT/'evidence/importer-loud-fail/r166/native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(r['old_zero_phase'],{'samples':30,'exact':30})
        self.assertEqual(sum(v['exact'] for v in r['rows']),102400)
        self.assertTrue(r['zero_phase_scale_paths_exact'])
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
