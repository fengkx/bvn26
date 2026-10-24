import gzip
import json
import unittest

from tools.probes.analyze_cxform_brackets import (
    EVIDENCE, MULTIPLIER_DELTAS, OFFSET_DELTAS, SITES, prior, read_native,
    read_offset_controls, sources,
)
from tools.probes.analyze_cxform_intervals import lower_bound
from tools.probes.analyze_cxform_rejected import measurements, rgb, sequence

ROOT = EVIDENCE/'r46'


class CxformBracketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.targets,cls.clipping,cls.centered = read_native(ROOT/'native')
        cls.offsets,cls.offset_report = read_offset_controls(ROOT/'offset')
        cls.report = json.loads(gzip.decompress((ROOT/'analysis.json.gz').read_bytes()))

    def test_fixed_source_grid_and_centered_native_rows(self):
        self.assertEqual((len(sources()),len(self.rows),len(self.targets),self.centered),(48,38400,1200,1536))
        self.assertEqual(self.clipping,[])
        grids = {}
        for v in self.targets:
            _,_,m,d,_ = SITES[v['site']]
            grids.setdefault(tuple(v['reference']),set()).add((v['multiplier']-m,v['offset_256']-d*256))
        self.assertEqual(len(grids),48)
        self.assertTrue(all(v=={(m,d) for m in MULTIPLIER_DELTAS for d in OFFSET_DELTAS} for v in grids.values()))
        for site,(a,_,_,_,_) in enumerate(SITES):
            self.assertEqual({v['source'][3] for v in self.targets if v['site']==site},set(range(a-4,a+5)))

    def test_signed_offset_property_is_fractional_but_native_draw_matches_truncation(self):
        self.assertEqual(len(self.offsets),2400)
        self.assertTrue(self.offset_report['property_fraction_preserved'])
        self.assertEqual(self.offset_report['truncation_exact'],2400)
        self.assertFalse(self.offset_report['failures'])
        self.assertTrue(any(d>0 and d!=int(d) for _,_,_,_,_,d,_ in self.offsets))
        self.assertTrue(any(d<0 and d!=int(d) for _,_,_,_,_,d,_ in self.offsets))

    def test_raw_and_integer_offset_bounds_preserve_all_prior_witnesses(self):
        old = prior()
        native = {tuple(key):(list(args),target) for key,args,target in
                  list(rgb(self.rows,'brackets'))+list(rgb(self.offsets,'offset'))}
        for integer,report in ((False,self.report),(True,self.report['truncated_offset_candidate'])):
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
                            if w['key'][0]=='r45':
                                self.assertEqual(w['key'][1:],previous[field]['key'])
                                self.assertEqual(bounds[bound],previous[bound])
                            else:
                                args,target = native[tuple(w['key'])]
                                args = list(args)
                                if integer:
                                    args[3] = int(args[3])
                                self.assertEqual((w['args'],w['native_channel']),(args,target))
                                self.assertEqual(lower_bound(tuple(args),space,order,target+step)-step,bounds[bound])
                if order=='alpha_first':
                    self.assertEqual(model['total_constraints'],1224288)
        raw = self.report['models']['unit/alpha_first']['combined_intervals']['49']
        self.assertGreater(raw['low_bits'],raw['high_bits'])

    def test_global_offset_rule_does_not_admit_a_failed_reciprocal_sequence(self):
        tables = measurements(EVIDENCE/'r44')
        adjusted = self.report['truncated_offset_candidate']
        for key,score in adjusted['target_sequences'].items():
            mode,order = key.split('/')
            count = 0
            for v in self.targets:
                args = (v['source'][1],v['source'][3],v['multiplier'],int(v['offset_256']/256),v['opacity'])
                count += sequence(args,tables[mode],order)==v['native'][1]
            self.assertEqual(score['exact'],count)
            self.assertLess(count,1200)
            self.assertEqual(adjusted['direct_sequences'][key]['old'],self.report['direct_sequences'][key]['old'])
        for report in (self.report,adjusted):
            for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
                self.assertFalse(report[flag])
