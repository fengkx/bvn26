"""Explicit self references cannot bypass nested timeline ownership requirements."""
import unittest
from tools.importer.visual_control_guard import requirements, validate_requirements


class QualifiedSelfControlTests(unittest.TestCase):
    def test_explicit_self_calls_require_owner_with_source_location(self):
        for source in ('this.stop();','this.play();','this.gotoAndPlay(12);',
                       'this.gotoAndStop("end");','this.gotoAndPlay(target + 1);',
                       'this . stop();'):
            bundle={'game_file':'game/fighter/fixture.swf','swf_sha256':'source-hash',
                    'scripts':[{'path':'DefineSprite_17/frame_9/DoAction.as','source':source}]}
            catalog=requirements(bundle)
            self.assertEqual(len(catalog['records']),1)
            timeline={'source_swf':{'sha256':'source-hash'},'definitions':[
                {'character_id':17,'display_list_frame_events':[[] for _ in range(9)]}]}
            with self.subTest(source=source),self.assertRaisesRegex(
                    ValueError,r'fixture.swf/DefineSprite_17/frame_9/DoAction.as: unsupported nested playhead'):
                validate_requirements(timeline,catalog,delegates=[])

    def test_bare_owned_stop_still_matches_exact_events(self):
        bundle={'game_file':'fixture.swf','swf_sha256':'hash','scripts':[
            {'path':'DefineSprite_17/frame_1/DoAction.as','source':'stop();'}]}
        timeline={'source_swf':{'sha256':'hash'},'definitions':[
            {'character_id':17,'display_list_frame_events':[[{'visual_controls':[{'op':'stop'}]}]]}]}
        validate_requirements(timeline,requirements(bundle),delegates=[])

    def test_unrelated_member_calls_are_not_misidentified_as_self(self):
        bundle={'game_file':'fixture.swf','swf_sha256':'hash','scripts':[
            {'path':'DefineSprite_17/frame_1/DoAction.as','source':'other.stop(); this.child.play();'}]}
        self.assertEqual(requirements(bundle)['records'],[])
