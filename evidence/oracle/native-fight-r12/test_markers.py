import copy
import unittest
from build_observer import r08,patch_source,FRAME,START,MENU,INSERTIONS
from analyze import validate_boundary,KINDS


class StartFightTests(unittest.TestCase):
    def setUp(self):self.source=r08.patch_sources(r08.r07.sources('scripts/main.json'),'m002-r12-test-fixture')[FRAME]

    def test_restore_all_original_operations_exactly(self):
        patched=patch_source(self.source)
        restored=patched.replace('\n'+INSERTIONS[4],'')
        for marker in INSERTIONS:restored=restored.replace(marker,'')
        self.assertEqual(restored,self.source)
        for operation in ['_root.setMenuEnable(true);','_menuEnabled = v;','_root.zhanting = false;','_root.readying = false;']:
            self.assertEqual(patched.count(operation),self.source.count(operation))

    def test_each_missing_or_duplicate_body_fails(self):
        for body in [START,MENU]:
            for replacement in ['',body+body]:
                with self.subTest(body=body,replacement=replacement),self.assertRaises(ValueError):patch_source(self.source.replace(body,replacement))

    def test_collision_refused(self):
        with self.assertRaises(ValueError):patch_source(self.source+'\n// startfight-entry')

    def fixture(self):
        data=['true,true,false,false,true,56','false,false,false,false,true,56','true,false,false','true,true,false','true,true,false','false,false,true,false,true,56']
        return [dict(kind=k,data=d) for k,d in zip(KINDS,data)]

    def test_synthetic_shape_does_not_prove_global_tick_or_admission(self):
        r=validate_boundary(self.fixture())
        self.assertTrue(r['source_boundary_shape_observed'])
        self.assertFalse(r['certified_global_tick'])
        self.assertFalse(r['oracle_accepted'])

    def test_missing_return_reorder_and_duplicate_refused(self):
        events=self.fixture()
        for bad in [events[:-1],events[::-1],events+[events[-1]],[]]:
            with self.subTest(events=bad),self.assertRaises(ValueError):validate_boundary(bad)

    def test_menu_and_readying_result_must_be_actual_matching_fields(self):
        for i,data in [(1,'false,true,false,false,true,56'),(3,'true,false,false'),(4,'true,undefined,false'),(5,'false,false,false,false,true,56')]:
            events=copy.deepcopy(self.fixture());events[i]['data']=data
            with self.subTest(index=i),self.assertRaises(ValueError):validate_boundary(events)


if __name__=='__main__':unittest.main()
