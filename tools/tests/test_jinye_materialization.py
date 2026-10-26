"""The new native boundary is explicit and source-derived, not inferred caching."""
import json
from fractions import Fraction as Q
import unittest
from tools.probes.build_bound_bitmap_component import ROOT
from tools.probes.build_jinye_materialization import allocation_for
from tools.probes.analyze_jinye_smooth_leaf import compose,transform


class JinyeMaterialization(unittest.TestCase):
    def setUp(self):
        self.fixture=json.loads((ROOT/'evidence/importer-loud-fail/r221/native/fixture.json').read_text())
        self.spec=self.fixture['cases'][0];self.shape=next(s for s in self.fixture['shapes'] if s['id']==56)

    def test_bounds_are_source_derived(self):
        bounds,polygon=allocation_for(self.spec,self.shape)
        self.assertEqual(bounds,[280,219,170,94])
        x,y,w,h=bounds
        self.assertTrue(all(x<=p[0]<x+w and y<=p[1]<y+h for p in polygon))

    def test_outer_draw_does_not_select_local_allocation(self):
        modified={**self.spec,'outer':[1,0,0,1,999,999],'draw':[3,0,0,3,-100,-100]}
        self.assertEqual(allocation_for(modified,self.shape),allocation_for(self.spec,self.shape))

    def test_integer_rebase_preserves_child_coordinates(self):
        bounds,_=allocation_for(self.spec,self.shape);x,y,_,_=bounds
        original=[Q(str(v)) for v in self.spec['matrix']];local=original.copy();local[4]-=x;local[5]-=y
        restored=compose([1,0,0,1,x,y],local)
        self.assertEqual(restored,original)


if __name__=='__main__':unittest.main()
