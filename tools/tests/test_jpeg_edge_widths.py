import gzip
import json
import unittest
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.build_jpeg_edge_widths import cases
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


class JpegEdgeWidthTests(unittest.TestCase):
    def test_entropy_preserving_widths_and_original_baseline(self):
        evidence=ROOT/'evidence/importer-loud-fail/r217'
        summary=json.loads(gzip.decompress((evidence/'summary.json.gz').read_bytes()))
        self.assertEqual([c for c,_,_ in cases()],json.loads((evidence/'native/build.json').read_text())['cases'])
        targets=[]
        for kind,data in events(evidence/'native'):
            if kind=='case':targets.append([])
            elif kind=='row':targets[-1].extend(unpack(list(map(int,data.split(',')))[1:]))
        old=[]
        for _,data in events(ROOT/'evidence/importer-loud-fail/r210/native')[1:-1]:old.extend(unpack(list(map(int,data.split(',')))[1:]))
        self.assertEqual(targets[0],old)
        for row,target in zip(summary['overlap_vs_width192'],targets[1:-1]):
            width=row['width']
            exact=sum(p==targets[-1][(i//width)*192+i%width] for i,p in enumerate(target))
            self.assertEqual(exact,row['exact'])
        self.assertFalse(summary['production_admitted'])
