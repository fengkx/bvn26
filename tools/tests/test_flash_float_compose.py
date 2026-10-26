import unittest
from fractions import Fraction
from tools.probes.model_flash_float_compose import compose_float, scene_matrix, f32, as_float, authored_twips, bits


def matrix(linear=(1,0,0,1),translation=(0,0),flags=1):
    return {'linear':list(linear),'translation':list(translation),'flags':flags}


class FloatComposeTests(unittest.TestCase):
    def test_products_round_before_addition_not_fused(self):
        epsilon=2**-23
        result=compose_float(matrix((1-epsilon,1,0,1)),matrix((1+epsilon,0,-1,1)))
        self.assertEqual(result['linear'][0],0)
        self.assertNotEqual(Fraction(result['linear'][0]),-Fraction(1,2**46))

    def test_translation_rounds_before_parent_integer_add(self):
        self.assertEqual(compose_float(matrix(translation=(1,3)),matrix((.5,0,0,.5),(1,1)))['translation'],[1,3])
        self.assertEqual(compose_float(matrix(translation=(-1,-3)),matrix((.5,0,0,.5)))['translation'],[0,-2])
        self.assertEqual(compose_float(matrix(translation=(1,0)),matrix(translation=(2**31-1,0)))['translation'][0],-2**31)

    def test_negative_zero_cross_terms_take_general_bitwise_branch(self):
        result=compose_float(matrix((1,-0.0,0,1)),matrix((1,-0.0,0,1)))
        self.assertEqual(bits(result['linear'][1]),0x80000000)

    def test_fixed_conversion_and_branch_scope(self):
        fixed=matrix((65537,0,0,65536),flags=0)
        self.assertEqual(as_float(fixed)['linear'][0],1+2**-16)
        with self.assertRaises(ValueError):compose_float(fixed,fixed)
        with self.assertRaises(ValueError):f32(float('nan'))
        with self.assertRaises(ValueError):f32(2**-140)
        with self.assertRaises(ValueError):f32(2**-200)
        with self.assertRaises(ValueError):f32(2**-150)

    def test_display_twips_to_pixels_units_preserve_identity(self):
        spec={'draw':[1,0,0,1,0,0],'outer':[1,0,0,1,0,0],'matrix':[1,0,0,1,0,0]}
        shape={'bitmap_matrix':{'scaleX':'20','scaleY':'20'}}
        result,metadata=scene_matrix(spec,shape)
        # f32(1/5)*5 is the declared constructor hypothesis, not exact rational1.
        self.assertEqual(result,[Fraction(f32(.2))*5,0,0,Fraction(f32(.2))*5,0,0])
        self.assertFalse(metadata['mxcsr_rtne_observed'])
        self.assertEqual(authored_twips(-.05),-1)
        with self.assertRaises(ValueError):authored_twips(.051)
