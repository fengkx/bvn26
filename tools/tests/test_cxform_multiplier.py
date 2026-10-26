import gzip
import json
import unittest

from tools.probes.analyze_cxform_multiplier import (
    DELTAS, EVIDENCE, SITES, previous_report, read_native, read_signed,
)
from tools.probes.analyze_cxform_intervals import lower_bound
from tools.probes.analyze_cxform_rejected import measurements, rgb, sequence

ROOT = EVIDENCE/'r47'


class CxformMultiplierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.targets,cls.clipping,cls.centered = read_native(ROOT/'native')
        cls.signed = read_signed(ROOT/'signed')
        cls.report = json.loads(gzip.decompress((ROOT/'analysis.json.gz').read_bytes()))

    def test_fixed_source_property_and_center_controls(self):
        self.assertEqual((len(self.rows),len(self.targets),self.centered),(19968,624,1536))
        self.assertFalse(self.clipping)
        self.assertTrue(self.report['property_fraction_preserved'])
        grids = {}
        for v in self.targets:
            base = SITES[v['site']][2]*256
            grids.setdefault(tuple(v['reference']),set()).add(v['multiplier_65536']-base)
        self.assertEqual(len(grids),48)
        self.assertTrue(all(v==set(DELTAS) for v in grids.values()))
        for site,(a,_,_,_,_) in enumerate(SITES):
            self.assertEqual({v['source'][3] for v in self.targets if v['site']==site},set(range(a-4,a+5)))

    def test_signed_native_anchors_discriminate_consumption_independently(self):
        self.assertEqual(len(self.signed),6240)
        self.assertTrue(self.report['signed_controls']['property_fraction_preserved'])
        anchors = self.report['signed_controls']['anchor_comparisons']
        self.assertEqual(anchors['toward_zero_8_8']['exact'],6240)
        self.assertEqual(anchors['floor_8_8']['exact'],5760)
        self.assertEqual(anchors['nearest_8_8']['exact'],5664)
        self.assertEqual(self.report['anchor_comparisons']['toward_zero_8_8']['exact'],19968)
        self.assertTrue(any(m<0 and m!=int(m) for _,_,_,_,m,_,_ in self.signed))

    def test_raw_and_quantized_witnesses_preserve_old_constraints(self):
        old = previous_report()
        native = {tuple(key):(list(args),target) for key,args,target in rgb(self.rows,'fine')}
        for quantized,report in ((False,self.report),(True,self.report['quantized_multiplier_candidate'])):
            for key,model in report['models'].items():
                space,order = key.split('/')
                for group in ('green_intervals','combined_intervals'):
                    if group not in model:
                        continue
                    for a,bounds in model[group].items():
                        previous = old['models'][key][group].get(a)
                        if previous:
                            self.assertGreaterEqual(bounds['low_bits'],previous['low_bits'])
                            self.assertLessEqual(bounds['high_bits'],previous['high_bits'])
                        for field,bound,step in (('lower_witness','low_bits',0),('upper_witness','high_bits',1)):
                            w = bounds[field]
                            if not w:
                                continue
                            if w['key'][0]=='r46_adjusted':
                                self.assertEqual(w['key'][1:],previous[field]['key'])
                                self.assertEqual(bounds[bound],previous[bound])
                            else:
                                args,target = native[tuple(w['key'])]
                                args = list(args)
                                if quantized:
                                    args[2] = int(args[2])
                                self.assertEqual((w['args'],w['native_channel']),(args,target))
                                self.assertEqual(lower_bound(tuple(args),space,order,target+step)-step,bounds[bound])
                if order=='alpha_first':
                    self.assertEqual(model['total_constraints'],1284192)
        self.assertTrue(self.report['models']['unit/alpha_first']['empty_combined_intervals'])

    def test_global_quantization_does_not_admit_failed_normalization(self):
        tables = measurements(EVIDENCE/'r44')
        adjusted = self.report['quantized_multiplier_candidate']
        for key,score in adjusted['target_sequences'].items():
            mode,order = key.split('/')
            count = 0
            for v in self.targets:
                args = (v['source'][1],v['source'][3],int(v['multiplier_65536']/256),v['offset'],v['opacity'])
                count += sequence(args,tables[mode],order)==v['native'][1]
            self.assertEqual(score['exact'],count)
            self.assertLess(count,624)
            self.assertEqual(adjusted['direct_sequences'][key]['old'],self.report['direct_sequences'][key]['old'])
        for report in (self.report,adjusted):
            for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
                self.assertFalse(report[flag])
        for report in self.report['signed_controls']['direct_sequences'].values():
            for group in report.values():
                self.assertEqual(group['channels'],18720)
                self.assertEqual(group['channels']-group['exact'],sum(v['occurrences'] for v in group['failures']))
