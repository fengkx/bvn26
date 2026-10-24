"""Signed reciprocal bounds must preserve every earlier native constraint."""
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.probes import cxform_signed_bounds as bounds
from tools.probes.analyze_cxform_intervals import channel, from_bits, lower_bound


class SignedBoundsTests(unittest.TestCase):
    def test_decreasing_endpoints_without_positive_search(self):
        bounds.interval.cache_clear()
        args = (25,49,-129,128,100)
        with patch.object(bounds,'lower_bound',side_effect=AssertionError('Positive search')):
            for space in ('unit','normalized','byte'):
                for order in ('alpha_first','opacity_first','joint'):
                    lo,hi = bounds.interval(args,space,order,12)
                    for bits in (lo,hi):
                        self.assertEqual(channel(args,from_bits(bits),space,order),12)
                    self.assertGreater(channel(args,from_bits(lo-1),space,order),12)
                    self.assertLess(channel(args,from_bits(hi+1),space,order),12)
                    for edge in (lo,hi):
                        for bits in range(edge-8,edge+9):
                            self.assertEqual(lo<=bits<=hi,
                                channel(args,from_bits(bits),space,order)==12)

    def test_positive_search_unchanged(self):
        args = (128,255,128,128,100)
        for space in ('unit','normalized','byte'):
            for order in ('alpha_first','opacity_first','joint'):
                self.assertEqual(bounds.interval(args,space,order,191),
                    (lower_bound(args,space,order,191),lower_bound(args,space,order,192)-1))

    def test_constant_channels_and_invalid_inputs(self):
        for args in ((25,49,0,128,100),(0,49,-129,128,100)):
            target = channel(args,0,'unit','alpha_first')
            self.assertEqual(bounds.interval(args,'unit','alpha_first',target),(0,bounds.MAX_FINITE))
            lo,hi = bounds.interval(args,'unit','alpha_first',target+1)
            self.assertGreater(lo,hi)
            with self.assertRaises(ValueError):
                bounds.first_at_most(args,'unit','alpha_first',target)
        for args in ((25,49,1.5,128,100),(25,49,-129,0.5,100),(25,0,1,0,100),
                     (25,49,1,float('nan'),100)):
            with self.assertRaises(ValueError):
                bounds.interval(args,'unit','alpha_first',12)

    def test_pinned_intersections_and_local_match_rejection(self):
        root = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail'
        current = json.loads(gzip.decompress((root/'r48/analysis.json.gz').read_bytes()))
        old = json.loads(gzip.decompress((root/'r47/analysis.json.gz').read_bytes()))['quantized_multiplier_candidate']
        self.assertEqual(current['old_constraints']+current['signed_constraints'],1302912)
        for key,model in current['models'].items():
            for group in ('green_intervals','combined_intervals'):
                if group not in model:
                    continue
                for alpha,interval in model[group].items():
                    previous = old['models'][key][group][alpha]
                    self.assertGreaterEqual(interval['low_bits'],previous['low_bits'])
                    self.assertLessEqual(interval['high_bits'],previous['high_bits'])
                    self.assertLessEqual(interval['low_bits'],interval['high_bits'])
        site = current['alpha49_discriminator'][0]
        local = site['constructions']['estimate_inverse']
        self.assertEqual(local['actual'],12)
        self.assertGreater(local['coefficient_bits'],site['intersection_high_bits'])
        for flag in ('candidate_admitted','gpu_advance_allowed','production_admitted'):
            self.assertFalse(current[flag])
        for score in current['direct_sequences'].values():
            self.assertEqual(score['signed']['exact'],18688)


if __name__=='__main__':
    unittest.main()
