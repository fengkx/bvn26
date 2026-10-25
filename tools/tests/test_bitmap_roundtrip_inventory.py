import hashlib
import json
from pathlib import Path
import struct
import unittest
import zlib
from tools.probes.inventory_bitmap_roundtrip import inventory, decode_lossless

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r88'


class BitmapRoundtripInventoryTests(unittest.TestCase):
    def test_all_component_lossless_texels_roundtrip_without_alpha_ambiguity(self):
        r = inventory()
        self.assertEqual(r, json.loads((EVIDENCE / 'inventory.json').read_text()))
        self.assertFalse(r['production_admitted'])
        for score in r['summary'].values():
            self.assertEqual(score, {'exact_texels':1031306,'texels':1031306,'exact_bitmaps':21,'bitmaps':21})
        self.assertEqual([(row['source'],row['bitmap']) for row in r['unmeasured']],
                         [('game/fighter/fz/jinye.swf',55),('game/fighter/orochimaru.swf',340)])
        for row in r['rows']:
            if row['status']=='measured':
                self.assertLessEqual(set(row['alpha_histogram']),{'0','255'})

    def test_palette_stride_and_rejection_boundaries(self):
        header=struct.pack('<HBHHB',7,3,1,2,1)
        palette=bytes([0,0,0,0,10,20,30,128])
        payload=header+zlib.compress(palette+bytes([1,0,0,0,0,0,0,0]))
        self.assertEqual(decode_lossless(payload),(7,1,2,[[10,20,30,128],[0,0,0,0]]))
        with self.assertRaisesRegex(ValueError,'Palette index'):
            decode_lossless(header+zlib.compress(palette+bytes([2,0,0,0,0,0,0,0])))
        with self.assertRaisesRegex(ValueError,'length'):
            decode_lossless(header+zlib.compress(palette+bytes([1,0])))
        with self.assertRaisesRegex(ValueError,'Non-premultiplied'):
            decode_lossless(struct.pack('<HBHH',7,5,1,1)+zlib.compress(bytes([1,255,0,0])))

    def test_source_assets_and_independent_reader_evidence_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
