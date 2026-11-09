import unittest
from build_observer import r07,patch_sources,LOADER,INIT,REQUEST,HP,CALLBACK,REQUEST_MARK,CALLBACK_ENTRY,CALLBACK_EXIT,hp_marker,root_action


class MarkerTests(unittest.TestCase):
    def setUp(self):self.source=r07.sources('scripts/main.json')

    def test_original_operations_and_short_circuit_unchanged(self):
        edited=patch_sources(self.source,'m002-r08-test-fixture')
        restored=edited[LOADER].replace(REQUEST_MARK,'').replace(CALLBACK_ENTRY,'').replace(CALLBACK_EXIT,'')
        self.assertEqual(restored,r07.base.patch_sources(self.source,'m002-r08-test-fixture')[LOADER])
        restored=edited[INIT].replace(hp_marker('before'),'').replace('\n'+hp_marker('after'),'')
        self.assertEqual(restored,self.source[INIT])
        self.assertEqual(edited[LOADER].count(REQUEST),1)
        self.assertEqual(edited[INIT].count(HP),1)

    def test_hp_snapshots_bracket_assignment_without_filtering(self):
        edited=patch_sources(self.source,'m002-r08-test-fixture')[INIT]
        self.assertIn(hp_marker('before')+HP+'\n'+hp_marker('after'),edited)
        self.assertNotIn('if(',hp_marker('before'))

    def test_missing_or_duplicate_boundaries_refused(self):
        for path,marker in [(LOADER,REQUEST),(LOADER,CALLBACK),(INIT,HP)]:
            for replacement in ['',marker+marker]:
                source=dict(self.source);source[path]=source[path].replace(marker,replacement)
                with self.subTest(path=path,replacement=replacement),self.assertRaises(ValueError):patch_sources(source,'m002-r08-test-fixture')

    def test_cannot_claim_load_init_from_load_complete(self):
        with self.assertRaisesRegex(ValueError,'No existing onLoadInit'):patch_sources(self.source,'m002-r08-test-fixture',require_on_load_init=True)
        source=dict(self.source);source[LOADER]+='\nLO.onLoadInit = function() {};'
        with self.assertRaisesRegex(ValueError,'re-audit'):patch_sources(source,'m002-r08-test-fixture')

    def test_original_r07_fighter_forwarders_remain(self):
        edited,sites=r07.patch_fighter(r07.sources('scripts/fighter/yihu.json'))
        self.assertEqual(len(sites),39)
        self.assertIn('decision-installed',edited)
        self.assertIn('yihu-sprite16',edited)

    def test_ambiguous_root_frame_action_refused(self):
        with self.assertRaises(ValueError):root_action({'root/1:12':'a','root/2:12':'b'},1)


if __name__=='__main__':unittest.main()
