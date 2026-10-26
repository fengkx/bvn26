"""The complete diagnostic cannot admit empty frames or unproved cache boundaries."""
import unittest
from fractions import Fraction as Q
from tools.probes.run_jinye_wrapper_cpu import coverage,gate,matrix


class JinyeWrapperCPU(unittest.TestCase):
    def test_empty_image_does_not_admit(self):
        self.assertFalse(gate({'exact_images':1,'exact_active_images':0,'complete_wrapper_exact':False}))
        self.assertFalse(gate({'complete_wrapper_exact':True,'cache_allocation_admitted':False}))
        keys=('complete_wrapper_exact','sampler_admitted','cache_allocation_admitted','coverage_admitted','ratio_consumption_proved','stream_metadata_semantics_admitted','local_input_native_exact')
        for missing in keys:
            report=dict.fromkeys(keys,True);report[missing]=False
            self.assertFalse(gate(report),missing)

    def test_geometric_area_is_not_native_admission(self):
        square=[(Q(0),Q(0)),(Q(1),Q(0)),(Q(1),Q(1)),(Q(0),Q(1))]
        self.assertEqual(coverage(square,0,0),1)
        self.assertEqual(coverage(square,1,0),0)
        half=[(Q(0),Q(0)),(Q(1,2),Q(0)),(Q(1,2),Q(1)),(Q(0),Q(1))]
        self.assertEqual(coverage(half,0,0),Q(1,2))

    def test_source_matrix_twips_and_linear_encoding(self):
        got=matrix({'scaleX':'1.7548218','scaleY':'0.99334717','rotateSkew0':'0.05230713','rotateSkew1':'-0.029678345','translateX':'-6457','translateY':'-2377'})
        self.assertEqual(got,[Q(115004,65536),Q(3428,65536),Q(-1945,65536),Q(65100,65536),Q(-6457,20),Q(-2377,20)])


if __name__=='__main__':unittest.main()
