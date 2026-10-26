import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_component_shape_identity import analyze

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r125'


class ComponentShapeIdentityTests(unittest.TestCase):
    def test_primitive_lookup_alias_does_not_erase_authored_matrix(self):
        result=analyze(EVIDENCE/'native')
        self.assertEqual(result,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertTrue(result['primitive_depth_returns_owner'])
        self.assertTrue(result['dynamic_movieclip_control_distinct'])
        self.assertFalse(result['primitive_readback_is_inner_transform'])
        self.assertEqual(result['authored_inner_matrix']['translateX'],'-17')
        self.assertEqual(result['authored_fill_matrix']['translateX'],'17')
        self.assertFalse(result['source_derived_input_verified'])
        self.assertFalse(result['production_admitted'])

    def test_sources_and_native_readbacks_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
