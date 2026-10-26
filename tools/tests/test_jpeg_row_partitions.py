import gzip
import json
import unittest
from unittest.mock import patch
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.build_jpeg_row_partitions import controls
from tools.probes.analyze_jpeg_row_partitions import routed_rgb
from tools.probes.analyze_bitmap_cache_support_local import events
from tools.probes.validate_jpeg_row_route import validate


class JpegRowPartitionTests(unittest.TestCase):
    def test_independent_geometry_and_color_controls(self):
        evidence=ROOT/'evidence/importer-loud-fail/r218'
        summary=json.loads(gzip.decompress((evidence/'summary.json.gz').read_bytes()))
        authored=[c for c,_ in controls()]
        self.assertEqual(authored,json.loads((evidence/'native/build.json').read_text())['cases'])
        targets=[]
        for kind,data in events(evidence/'native'):
            if kind=='case':targets.append([])
            elif kind=='row':targets[-1].extend([[(v>>s)&255 for s in (16,8,0)] for v in map(int,data.split(',')[1:])])
        for row in summary['rows']:
            case=row['case'];actual=[routed_rgb(case['ycbcr'],i%case['width'],case['width'],row['group']) for i in range(len(targets[case['id']]))]
            self.assertEqual(sum(a==b for a,b in zip(actual,targets[case['id']])),row['exact'])
        self.assertEqual(summary['exact_by_group']['8'],110592)
        self.assertFalse(summary['production_admitted'])

    def test_heldout_original_and_widths_are_exact(self):
        evidence=ROOT/'evidence/importer-loud-fail/r218'
        result=validate(evidence/'heldout-planes')
        self.assertEqual(result,json.loads((evidence/'heldout.json').read_text()))
        self.assertEqual(result['exact'],494424)
        self.assertFalse(result['production_admitted'])

    def test_heldout_rejects_incomplete_or_reordered_native_readback(self):
        evidence=ROOT/'evidence/importer-loud-fail/r218'
        original=list(events(ROOT/'evidence/importer-loud-fail/r217/native'))
        last_case=max(i for i,(kind,_) in enumerate(original) if kind=='case')
        first_row=next(i for i,(kind,_) in enumerate(original) if kind=='row')
        truncated_row=original.copy()
        kind,data=truncated_row[first_row]
        truncated_row[first_row]=(kind,data.rsplit(',',1)[0])
        reordered=original.copy()
        reordered[first_row],reordered[first_row+1]=reordered[first_row+1],reordered[first_row]
        malformed={
            'missing case':original[:last_case]+original[-1:],
            'missing row':original[:first_row]+original[first_row+1:],
            'truncated row':truncated_row,
            'reordered rows':reordered,
            'missing done':original[:-1],
        }
        for name,readback in malformed.items():
            with self.subTest(name=name), patch('tools.probes.validate_jpeg_row_route.events',return_value=iter(readback)):
                with self.assertRaises(AssertionError):
                    validate(evidence/'heldout-planes')
