"""Keep source-mask and scope guards independent of native output images."""
import copy
import hashlib
import json
import unittest
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.run_orochimaru_wrapper import sampling, compare, compare_boundaries


class OrochimaruWrapperTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads((ROOT/'evidence/importer-loud-fail/r32/components/orochimaru/cases.json').read_text())[0]
        self.leaf = {'inner_matrix':{'translateX':'-1860','translateY':'-7560'}}

    def test_preserves_outer_and_inner_translations(self):
        metadata, packed, coordinates = sampling(self.case,self.leaf)
        self.assertEqual(metadata['filters'],self.case['placement']['filters'])
        width,height = metadata['size']
        self.assertEqual(len(packed),width*height*32)
        self.assertEqual(len(coordinates),width*height*16)
        self.assertEqual(metadata['key'][15:17],['300.0','46.03174603174605'])

    def test_native_boundaries_precede_complete_image_admission(self):
        evidence = ROOT/'evidence/importer-loud-fail/r219'
        stored = json.loads((evidence/'gpu/report.json').read_text())
        boundaries = compare_boundaries(evidence/'gpu', evidence/'native')
        images = compare(evidence/'gpu')
        self.assertEqual(boundaries['boundaries'], stored['boundaries'])
        self.assertEqual(images['images'], stored['images'])
        self.assertTrue(boundaries['boundaries_exact'])
        self.assertEqual(sum(r['samples'] for r in boundaries['boundaries']), 702535)
        self.assertEqual(images['exact_images'], 10)
        self.assertFalse(stored['production_admitted'])
        proof = json.loads((evidence/'gpu/provenance.json').read_text())
        for name, digest in proof['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), digest)
        for name, digest in proof['readback_sha256'].items():
            path = evidence/'gpu'/name
            if path.exists():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_rejects_unproven_filter_and_affine(self):
        for field,value in [('hasRotate','true'),('hasScale','true')]:
            case=copy.deepcopy(self.case); case['placement']['matrix'][field]=value
            with self.assertRaises(AssertionError): sampling(case,self.leaf)
        case=copy.deepcopy(self.case); case['placement']['filters'][0]['blurY']=21
        with self.assertRaises(AssertionError): sampling(case,self.leaf)


if __name__ == '__main__': unittest.main()
