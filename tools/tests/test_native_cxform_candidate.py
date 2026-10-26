"""Native-byte arithmetic must clear every retained control before GPU work."""
import gzip
import json
from pathlib import Path
import unittest
from tools.probes.native_cxform_candidate import channel, construction, bounded
from tools.probes.analyze_cxform_intervals import f32, float_bits, from_bits


class NativeCxformCandidateTests(unittest.TestCase):
    def test_independent_construction_and_unique_hardware_inverse(self):
        constants,reciprocals,witnesses = construction()
        self.assertEqual(float_bits(constants['denominator_bias']),0x37808081)
        self.assertEqual(set(reciprocals),set(range(1,256)))
        for alpha,witness in witnesses.items():
            expected = float_bits(f32(f32(alpha*constants['normalizer'])+constants['denominator_bias']))
            self.assertEqual(witness['denominator_bits'],expected)
            first,last,output = witness['hardware_run']
            self.assertLessEqual(first,expected)
            self.assertLessEqual(expected,last)
            bits = witness['reciprocal_bits']
            if witness['source']=='r57_unique_inverse':
                self.assertEqual(float_bits(f32(from_bits(bits)*255)),output)
                for adjacent in (-1,1):
                    self.assertNotEqual(float_bits(f32(from_bits(bits+adjacent)*255)),output)
            else:
                self.assertEqual(bits,output)

    def test_signed_and_old_positive_witnesses(self):
        for args,native in (((25,49,-129,128,100),12),((23,49,2046,-894,100),11),
                            ((31,33,256,-4,33),9),((164,204,192,0,100),123),
                            ((103,204,2047,-897,100),105)):
            self.assertEqual(channel(args),native)
        with self.assertRaises(ValueError):
            channel((25,49,1.5,128,100))
        with self.assertRaises(ValueError):
            bounded([1,2,3,4],100,16,16)

    def test_complete_cpu_gate_and_native_boundaries(self):
        path = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r58/analysis.json.gz'
        report = json.loads(gzip.decompress(path.read_bytes()))
        self.assertEqual(sum(v['channels'] for v in report['scores'].values()),1302912)
        for value in report['scores'].values():
            self.assertEqual(value['exact'],value['channels'])
            self.assertEqual(value['failures'],[])
        for name,value in report['prior_regressions']['scores'].items():
            if name=='exact_reciprocal_negative_control':
                self.assertLess(value['exact'],value['pixels'])
            else:
                self.assertEqual(value['exact'],value['pixels'])
        self.assertEqual(report['prior_regressions']['scores']['native_buffer_boundaries']['exact'],43200)
        for flag in ('cpu_arithmetic_passed','candidate_admitted','gpu_advance_allowed'):
            self.assertTrue(report[flag])
        self.assertFalse(report['production_admitted'])
        self.assertFalse(report['execution_routing_verified'])

    def test_scalar_tail_and_all_alpha_regressions(self):
        path = Path(__file__).resolve().parents[2]/'evidence/importer-loud-fail/r58/analysis.json.gz'
        r = json.loads(gzip.decompress(path.read_bytes()))
        for value in (r['all_alpha'],r['nonbinary_opacity'],r['geometry']['intersection_135'],r['geometry']['intersection_197']):
            self.assertEqual(value['exact'],value['pixels'])
            self.assertEqual(value['max_channel_delta'],[0]*4)
        self.assertEqual(bounded([0,0,0,0],100,16,0),[0]*4)


if __name__=='__main__':
    unittest.main()
