import gzip
import json
import unittest
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.build_jpeg_low_luma import controls
from tools.probes.analyze_jpeg_color_sequences import rgb
from tools.probes.analyze_bitmap_cache_support_local import events


class JpegLowLumaTests(unittest.TestCase):
    def test_constants_reject_low_luma_patch(self):
        evidence=ROOT/'evidence/importer-loud-fail/r216'
        summary=json.loads(gzip.decompress((evidence/'summary.json.gz').read_bytes()))
        authored=[c for c,_ in controls()]
        self.assertEqual(authored,json.loads((evidence/'native/build.json').read_text())['cases'])
        index=-1;count=0
        for kind,data in events(evidence/'native'):
            if kind=='case':index+=1
            elif kind=='row':
                expected=rgb(authored[index]['ycbcr'],'floor-contributions')
                for value in map(int,data.split(',')[1:]):
                    self.assertEqual([(value>>s)&255 for s in (16,8,0)],expected);count+=1
        self.assertEqual(count,114688)
        self.assertEqual(summary['exact'],count)
        self.assertFalse(summary['production_admitted'])
