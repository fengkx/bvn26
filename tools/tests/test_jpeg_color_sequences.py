import gzip
import json
import unittest
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jpeg_color_sequences import rgb
from tools.probes.analyze_bitmap_cache_support_local import events


class JpegColorSequenceTests(unittest.TestCase):
    def test_fixed_sequence_against_retained_independent_planes(self):
        evidence=ROOT/'evidence/importer-loud-fail/r213'
        summary=json.loads(gzip.decompress((evidence/'summary.json.gz').read_bytes()))
        targets=[]
        for kind,data in events(ROOT/'evidence/importer-loud-fail/r212/native'):
            if kind=='case':targets.append([])
            elif kind=='row':targets[-1].extend([[(v>>s)&255 for s in (16,8,0)] for v in map(int,data.split(',')[1:])])
        for row in summary['rows']:
            case=row['case']['id'];values=list(Image.open(evidence/'planes'/f'{case}.ycbcr.ppm').getdata())
            actual=[rgb(v,row['sequence']) for v in values]
            self.assertEqual(sum(a==b for a,b in zip(actual,targets[case])),row['exact'])
        self.assertEqual(summary['exact_by_sequence']['floor-contributions'],6144)
        self.assertFalse(summary['production_admitted'])
