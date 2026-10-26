import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_bitmap_cache_support_grid import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r116'


class BitmapCacheSupportGridTests(unittest.TestCase):
    def test_independent_support_rejects_simple_expansions(self):
        result=analyze(EVIDENCE/'native')
        self.assertEqual(result,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        self.assertEqual(result['source_exact'],480)
        self.assertEqual(result['alpha_independent_groups'],648)
        self.assertEqual({name:m['exact'] for name,m in result['models'].items()},
                         {'unexpanded':432,'source_one_twip':656,'device_one_subpixel':784,'separate_geometry_translation':1296})
        self.assertFalse(result['candidate_admitted'])
        self.assertFalse(result['production_admitted'])

    def test_sources_and_readbacks_are_pinned(self):
        provenance=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
