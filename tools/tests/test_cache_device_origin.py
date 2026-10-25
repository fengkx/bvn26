import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_cache_device_origin import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r112'


class CacheDeviceOriginTests(unittest.TestCase):
    def test_device_origin_improves_but_remains_rejected(self):
        r=analyze()
        self.assertEqual(r,json.loads(gzip.decompress((EVIDENCE/'analysis.json.gz').read_bytes())))
        expected={'r101':(37842,37842),'r102':(228317,240900),'r103':(68544,68544),'r104':(19980,19980),'r109':(14854,15048)}
        for suite,(exact,total) in expected.items():
            score=r['comparisons'][suite+'/device_consumed_bounds']
            self.assertEqual((score['exact'],score['samples']),(exact,total))
        for flag in ('specific_normalization_branch_verified','candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(r[flag])

    def test_sources_and_static_bytes_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
        static=json.loads((EVIDENCE/'static-binary.json').read_text())
        self.assertFalse(static['specific_normalization_branch_verified'])
        self.assertEqual(static['device_scale_constant']['bits'],'0x3d4ccccd')
