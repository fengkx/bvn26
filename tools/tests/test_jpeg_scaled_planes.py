import json
import unittest
from PIL import Image
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.analyze_jpeg_color_sequences import rgb
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.run_nested_filters import unpack


class JpegScaledPlaneTests(unittest.TestCase):
    def test_controls_exact_and_original_four_rejections_retained(self):
        evidence=ROOT/'evidence/importer-loud-fail/r215'
        summary=json.loads((evidence/'summary.json').read_text())
        targets=[]
        for kind,data in events(ROOT/'evidence/importer-loud-fail/r212/native'):
            if kind=='case':targets.append([])
            elif kind=='row':targets[-1].extend([[(v>>s)&255 for s in (16,8,0,24)] for v in map(int,data.split(',')[1:])])
        cases=[(f"control{r['case']['id']}",r['case']['subsampling'],targets[r['case']['id']],r['exact']) for r in summary['controls']]
        original=[]
        for _,data in events(ROOT/'evidence/importer-loud-fail/r210/native')[1:-1]:original.extend(unpack(list(map(int,data.split(',')))[1:]))
        cases.append(('original',2,original,70304))
        for folder,subsampling,target,expected in cases:
            base=evidence/'planes'/folder
            paths=[base/'scale1/c0.pgm']+[base/f"scale{2 if subsampling==2 else 1}/c{c}.pgm" for c in (1,2)]
            planes=[list(Image.open(p).getdata()) for p in paths]
            actual=[rgb(v,'floor-contributions') for v in zip(*planes)]
            self.assertEqual(sum(a==t[:3] or t[3]==0 for a,t in zip(actual,target)),expected)
        self.assertEqual(summary['control_exact'],12288)
        self.assertFalse(summary['production_admitted'])
