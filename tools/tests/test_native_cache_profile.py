import hashlib
import json
from pathlib import Path
import struct
import unittest
from tools.probes.analyze_native_cache_profile import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r111'


class NativeCacheProfileTests(unittest.TestCase):
    def test_sampled_callers_do_not_admit_a_normalization_branch(self):
        r=analyze(EVIDENCE)
        self.assertEqual(r,json.loads((EVIDENCE/'analysis.json').read_text()))
        self.assertEqual(list(r['profiles']['cached']['call_return_observations'].values()),[519,482,73,361])
        self.assertEqual(list(r['profiles']['uncached']['call_return_observations'].values()),[0,0,0,0])
        self.assertFalse(r['specific_normalization_branch_verified'])
        self.assertFalse(r['candidate_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_sources_profiles_and_call_instructions_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
        static=json.loads((EVIDENCE/'static-edges.json').read_text())
        for edge in static['call_edges']:
            raw=bytes.fromhex(edge['bytes']);self.assertEqual(raw[0],0xe8)
            self.assertEqual(int(edge['site'],16)+5+struct.unpack('<i',raw[1:])[0],int(edge['target'],16))
