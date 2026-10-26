import unittest
from fractions import Fraction as Q
from tools.probes.model_flash_float_compose import scene_matrix

class HierarchyTests(unittest.TestCase):
    def test_identity_units_preserve_authored_fill_precision(self):
        # A five-pixel draw scale gives an exactly representable twip→quarter
        # factor1; source fill translations must not be rounded to quarters.
        identity=[1,0,0,1,0,0]
        shape={'bitmap_matrix':{'scaleX':'20','scaleY':'20','translateX':'1','translateY':'-1'}}
        matrix,_=scene_matrix({'draw':[5,0,0,5,0,0],'outer':identity,'matrix':identity},shape)
        self.assertEqual(matrix,[Q(5),Q(0),Q(0),Q(5),Q(1,4),Q(-1,4)])

    def test_source_twips_are_not_silently_rounded(self):
        identity=[1,0,0,1,0,0]
        shape={'bitmap_matrix':{'scaleX':'20','scaleY':'20'}}
        with self.assertRaises(ValueError):scene_matrix({'draw':identity,'outer':identity,'matrix':[1,0,0,1,.001,0]},shape)

if __name__=='__main__':unittest.main()
