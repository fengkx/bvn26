"""Karin's authored healing, warps and base-form selection contract."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class KarinImportTests(unittest.TestCase):
    def test_receiver_matches_shared_source(self):
        bundles = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('karin', 'juggo')]
        self.assertEqual(bundles[0]['DefineSprite_2/frame_1/DoAction.as'],
                         bundles[1]['DefineSprite_2/frame_1/DoAction.as'])

    def test_source_healing_is_conditional_and_not_clamped(self):
        source = {s['path']: s['source'] for s in read('scripts/fighter/karin.json')['scripts']}
        model = read('godot/generated/fighters/karin/ai.json')
        for frame in range(763, 769):
            path = f'DefineSprite_427/frame_{frame}/DoAction.as'
            self.assertEqual(' '.join(source[path].split()), 'if(hp < 1000) { hp += 5; }')
            calls = model['frame_calls'].get(str(frame), [])
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]['conditions'], [{'field': 'hp', 'operator': 'lt', 'value': 1000}])
            self.assertEqual(calls[0]['calls'],
                             [{'op': 'frame_field', 'field_name': 'hp', 'operator': '+=', 'value': 5}])

    def test_super_frames_and_source_helper(self):
        model = read('data/actions/karin-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(607, 'super_start'), (650, 'super_end'), (697, 'super_start'),
                          (745, 'super_end'), (848, 'super_start'), (906, 'super_end')])
        catalog = read('manifest.json')['fighter_catalog']['香磷']
        self.assertNotIn('fzurl', catalog)
        self.assertEqual(catalog['fz'], '鼬')
        self.assertEqual(read('godot/generated/main/character_selection/available.json')['fighters']['香磷'], 'karin')
        self.assertIn('karin', read('services/matchmaking/src/catalog.json')['fighters'])

    def test_follow_calls_keep_second_action_tag_order(self):
        model = read('godot/generated/fighters/karin/ai.json')
        for frame, place_y, front_only in [(654, True, False), (908, False, True)]:
            calls = model['frame_calls'][str(frame)]
            self.assertEqual([call['op'] for call in calls], ['screen_flash', 'follow_clip'])
            self.assertEqual(calls[1]['path'], f'DefineSprite_427/frame_{frame}/DoAction_2.as')
            self.assertEqual((calls[1]['place_x'], calls[1]['place_y'], calls[1]['front_only']),
                             (True, place_y, front_only))

    def test_projectile_local_name_is_not_an_early_rename(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools/importer"))
        from build_combat_model import parse_clip_timeline
        from combat_projectile_parser import parse_projectile_motion
        bundle = read("scripts/fighter/karin.json")
        clip = parse_clip_timeline(bundle, 173)
        self.assertEqual(clip["initial_variables"],
                         {"movspeed": 20, "played": 0, "atm_name": "zh1atm"})
        self.assertEqual(clip["stop_frames"], [3, 12])
        self.assertEqual([event["frame"] for event in clip["rename_frames"]], [5, 8])
        self.assertEqual(clip["rename_frames"][0]["name_field"], "atm_name")
        source = next(script["source"] for script in bundle["scripts"]
                      if script["path"] == "DefineSprite_427/frame_454/PlaceObject2_173_28/CLIPACTIONRECORD onClipEvent(enterFrame).as")
        group = parse_projectile_motion(source)["on_hit_events"][0]
        self.assertEqual(group["writes"][-1], {"field": "atm_name", "value": "zh11atm"})
        self.assertEqual(group["goto_frame"], 5)
