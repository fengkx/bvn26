import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from tools.probes.analyze_indexed_header_control import analyze
from tools.probes.build_indexed_long_header import force_long
from tools.probes.native_lossless_tag import lossless2_tag
from tools.probes.build_minimal_swf import tag,rect
from tools.probes.build_bound_bitmap_component import source_tags

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r149'


class IndexedHeaderControlTests(unittest.TestCase):
    def test_valid_native_source_precedes_exact_scalar_claim(self):
        r=analyze(EVIDENCE/'native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertTrue(r['readback']['native_indexed_source_verified'])
        self.assertEqual(r['readback']['native_source']['exact'],2275)
        self.assertEqual(r['readback']['before_after_exact'],1152)
        for v in r['fixed_eight_bit_scalar'].values():self.assertEqual(v['exact'],1152)
        self.assertFalse(r['indexed_continuous_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_long_header_preserves_payload_and_other_tags(self):
        payload=struct.pack('<HBHH',7,3,35,65)+bytes(48)
        body=rect(0,20,0,20)+struct.pack('<HH',30*256,1)+tag(36,payload)+tag(1)+tag(0)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'control.swf';path.write_bytes(b'FWS\x08'+struct.pack('<I',len(body)+8)+body)
            original=list(source_tags(path));r=force_long(path);after=list(source_tags(path))
            self.assertEqual([(c,p) for c,p,_ in after],[(c,p) for c,p,_ in original])
            self.assertEqual(after[0][2],lossless2_tag(payload))
            self.assertEqual(r['other_tag_count'],2)
            with self.assertRaises(AssertionError):force_long(path)
        with self.assertRaisesRegex(ValueError,'locked source'):force_long(ROOT/'game/fighter/lanran.swf')
        with self.assertRaisesRegex(ValueError,'Truncated'):lossless2_tag(b'')

    def test_source_and_native_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
