import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_cache_affine_candidate import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r110'


class CacheAffineCandidateTests(unittest.TestCase):
    def test_static_candidates_remain_rejected(self):
        r = analyze()
        self.assertEqual(r,json.loads((EVIDENCE/'analysis.json').read_text()))
        for suite,samples,baseline,rejected in [('r104',19980,16379,12886),('r109',15048,10228,6564)]:
            for method in ('baseline','fixed_inverse_compose','float_inverse_compose'):
                score=r['comparisons'][suite+'/'+method]
                self.assertEqual(score['samples'],samples)
                self.assertEqual(score['exact'],baseline if method=='baseline' else rejected)
        for flag in ('static_routing_verified','candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(r[flag])

    def test_sources_readbacks_and_static_bytes_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
        static=json.loads((EVIDENCE/'static-binary.json').read_text())
        self.assertFalse(static['execution_routing_verified'])
        for span in static['spans'].values():
            raw=bytes.fromhex(span['bytes'])
            self.assertEqual(len(raw),int(span['end'],16)-int(span['start'],16))
            self.assertEqual(hashlib.sha256(raw).hexdigest(),span['sha256'])
