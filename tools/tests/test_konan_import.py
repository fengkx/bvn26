"""Konan base-form invariants from the locked Sprite 563 source."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class KonanImportTests(unittest.TestCase):
    def test_shared_controller_receiver_and_body(self):
        sources = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('konan', 'Renji')]
        for own, shared in ((16, 16), (2, 2), (563, 717)):
            self.assertEqual(sources[0][f'DefineSprite_{own}/frame_1/DoAction.as'],
                             sources[1][f'DefineSprite_{shared}/frame_1/DoAction.as'])

    def test_source_super_receiver_and_fallthrough_events(self):
        model = read('data/actions/konan-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual(model, read('godot/generated/fighters/konan/combat.json'))
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(624, 'super_start'), (638, 'super_end'),
                          (691, 'super_start'), (704, 'super_end'),
                          (775, 'super_start'), (790, 'super_end'),
                          (812, 'super_start'), (846, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']],
                         [(1077, False), (1090, True)])
        self.assertEqual([(e['frame'], e['xgtype']) for e in model['on_defence_frames']],
                         [(1065, 2)])
        self.assertEqual(model['action_exits']['被打']['frame'], 1086)
        self.assertEqual([(e['from'], e['to'], e['frame']) for e in model['timeline_fallthroughs']],
                         [('超必杀', '超必杀2', 912)])
        self.assertEqual(model['action_exits']['空中必杀']['target'], '超必杀2')

    def test_opening_and_source_identity(self):
        intro = read('godot/generated/fighters/konan/intro.json')
        self.assertEqual(intro['source_sprite_id'], 563)
        self.assertEqual(intro['state_frames'], {'1162': 1, '1164': 3, '1206': 2})
        catalog = read('manifest.json')['fighter_catalog']['小南']
        self.assertEqual(catalog['url'], 'konan.swf')
        self.assertEqual(read('godot/generated/main/character_selection/available.json')['fighters']['小南'], 'konan')
        self.assertIn('konan', read('services/matchmaking/src/catalog.json')['fighters'])

    def test_scaled_load_targeting_and_attack_name_release(self):
        model = read('data/actions/konan-base.json')
        placements = {e['frame']: e for e in model['clip_placements']}
        for frame in (496, 547, 707):
            event = placements[frame]
            self.assertTrue(event['front_only'])
            self.assertTrue(event['divide_parent_scale_x'])
            self.assertEqual(event.get('divide_parent_scale_y', False), frame != 496)
        hooks = read('godot/generated/fighters/konan/player_controller/controller.json')['projectile_hooks']
        hook = next(h for h in hooks if h['placement_frame'] == 496)
        self.assertEqual(hook['projectile']['instance_name'], 'zh2atm')
        self.assertEqual([(e['frame'], e['instance_name']) for e in hook['projectile']['rename_frames']],
                         [(6, 'abcd')])
        self.assertEqual(hook['projectile']['stop_frames'], [26])
