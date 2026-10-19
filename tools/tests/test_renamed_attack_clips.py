"""Independent attack-clip lifetime rules from the retained source timeline."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_controller import renamed_timeline_hooks


class RenamedAttackClipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / 'scripts/fighter/minren.json').read_text())
        cls.timeline = json.loads((ROOT / 'data/slices/minren-base.timeline.json').read_text())

    def test_source_renames_and_empty_terminal_frame(self):
        hooks = renamed_timeline_hooks(self.bundle, 764, self.timeline, [])
        hook = next(h for h in hooks if h['projectile']['character_id'] == 489)
        clip = hook['projectile']
        self.assertEqual([(r['frame'], r['instance_name']) for r in clip['rename_frames']],
                         [(11, 'sbsatm'), (24, 'sbs2atm')])
        self.assertEqual(clip['stop_frames'], [37])
        self.assertEqual(hook['member_frames'], list(range(683, 725)))
        definition = next(d for d in self.timeline['definitions'] if d['character_id'] == 489)
        self.assertEqual(definition['display_list_frames'][36], [])
        self.assertEqual([(e['frame'], e['op']) for e in clip['frame_events']],
                         [(30, 'screen_flash')])
        remaining = renamed_timeline_hooks(self.bundle, 764, self.timeline, [hook])
        self.assertNotIn(hook, remaining)
        # Sprite 260 starts as zh1atm and releases that name at local frame 5.
        self.assertEqual([h['projectile']['character_id'] for h in remaining], [260])
        self.assertEqual(renamed_timeline_hooks(self.bundle, 764, self.timeline, hooks), [])

    def test_replacement_does_not_share_the_old_playhead(self):
        placement = {'character_id': 489, 'depth': 7, 'name': 'future_attack', 'placed_frame': 20}
        timeline = {'definitions': self.timeline['definitions'], 'frames': [
            {'frame': 20, 'display_list': [placement]},
            {'frame': 21, 'display_list': [placement]},
            {'frame': 22, 'display_list': [{**placement, 'placed_frame': 22}]},
        ]}
        hooks = renamed_timeline_hooks(self.bundle, 999, timeline, [])
        self.assertEqual([h['member_frames'] for h in hooks], [[20, 21], [22]])
        self.assertNotEqual(hooks[0]['path'], hooks[1]['path'])
        self.assertEqual(hooks[1]['projectile']['instance_name'], 'future_attack')

    def test_unknown_frame_behavior_fails_compilation(self):
        bundle = copy.deepcopy(self.bundle)
        bundle['scripts'].append({'path': 'DefineSprite_489/frame_31/DoAction.as',
                                  'source': 'gotoAndPlay(5);'})
        with self.assertRaisesRegex(ValueError, 'Uncompiled renamed attack timeline'):
            renamed_timeline_hooks(bundle, 764, self.timeline, [])


if __name__ == '__main__':
    unittest.main()
