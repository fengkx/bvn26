import gzip
import json
import unittest
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jpeg_chroma_lattice import interpolate
from tools.probes.analyze_jpeg_color_sequences import rgb
from tools.probes.analyze_bitmap_cache_support_local import events


class JpegChromaLatticeTests(unittest.TestCase):
    def test_global_geometry_candidates_remain_rejected(self):
        evidence=ROOT/'evidence/importer-loud-fail/r214'
        summary=json.loads(gzip.decompress((evidence/'summary.json.gz').read_bytes()))
        targets=[]
        for kind,data in events(ROOT/'evidence/importer-loud-fail/r212/native'):
            if kind=='case':targets.append([])
            elif kind=='row':targets[-1].extend([[(v>>s)&255 for s in (16,8,0)] for v in map(int,data.split(',')[1:])])
        for row in summary['rows']:
            case=row['case']['id'];values=list(Image.open(evidence/'planes'/f'{case}.ycbcr.ppm').getdata())
            lattice=[values[y*32+x] for y in range(0,32,2) for x in range(0,32,2)]
            actual=[rgb([values[i][0]]+[interpolate(lattice,16,16,i%32,i//32,c,row['alignment'],row['rounding']) for c in (1,2)],'floor-contributions') for i in range(1024)]
            self.assertEqual(sum(a==b for a,b in zip(actual,targets[case])),row['exact'])
        self.assertFalse(summary['production_admitted'])
