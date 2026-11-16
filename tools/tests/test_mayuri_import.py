"""Mayuri's authored receiver, super lifecycle and default assist."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class MayuriImportTests(unittest.TestCase):
    def test_receiver_matches_shared_source(self):
        bundles = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('mayuri', 'juggo')]
        path = 'DefineSprite_2/frame_1/DoAction.as'
        self.assertEqual(bundles[0][path], bundles[1][path])

    def test_super_and_hurt_frames_follow_source(self):
        model = read('data/actions/mayuri-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual([(e['frame'], e['kind']) for e in model['super_events']],
                         [(494, 'bsd'), (522, 'bsw'), (578, 'bsd'),
                          (600, 'cbsw'), (743, 'cbsd'), (871, 'cbsw')])
        self.assertEqual([e['face_label'] for e in model['super_events'] if 'face_label' in e],
                         ['涅浊利1', '涅浊利1', '涅浊利2'])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']],
                         [(1057, False), (1070, True)])
        self.assertEqual(model['action_exits']['被打']['frame'], 1066)
        self.assertEqual(model['action_exits']['超必杀']['frame'], 975)

    def test_default_assist_is_existing_itachi(self):
        fighter = read('manifest.json')['fighter_catalog']['涅茧利']
        self.assertNotIn('fzurl', fighter)
        self.assertEqual(fighter['fz'], '鼬')
        available = read('godot/generated/main/character_selection/available.json')
        self.assertEqual(available['helpers'][fighter['fz']], 'you')

    def test_super_continuation_and_warp_keep_source_conditions(self):
        calls = read('godot/generated/fighters/mayuri/ai.json')['frame_calls']
        continuation = calls['623'][0]
        self.assertEqual(continuation['conditions'], [
            {'field': 'opponent_hp', 'operator': 'gt', 'value': 0},
            {'field': 'opponent_action', 'operator': 'eq', 'value': -1},
        ])
        self.assertEqual(continuation['calls'][0]['label'], '必杀2')
        warp = calls['528'][0]['warp']
        self.assertEqual(warp['xscale_lt_0'], {'set_xscale': 100.0, 'x_pixels': -20.0})
        self.assertEqual(warp['xscale_gt_0'], {'set_xscale': -100.0, 'x_pixels': 20.0})
        self.assertTrue(warp['place_y'])
        self.assertEqual(warp['y_pixels'], -20.0)

    def test_ranged_projectile_compiles_authored_hit_label_and_locals(self):
        model = read('data/actions/mayuri-base.json')
        projectile = next(p for p in model['projectiles'] if p['instance_name'] == 'abcd')
        self.assertEqual(projectile['initial_variables'], {'movspeed': 15.0, 'played': 0})
        self.assertNotIn(1, projectile['stop_frames'])
        self.assertEqual(projectile['on_hit_goto_frame'], 15)
        self.assertEqual(projectile['on_hit_goto_conditions'], [
            {'field': 'played', 'operator': '==', 'value': 0}])
        self.assertTrue(projectile['motion_after_collision'])
        self.assertEqual(projectile['local_motion_conditions'], [
            {'field': 'played', 'operator': '==', 'value': 0}])
        for event in projectile['rename_frames']:
            self.assertEqual(event['local_writes'], [{'field': 'played', 'value': 1}])

    def test_projectile_flashes_keep_source_colors(self):
        projectiles = read('data/actions/mayuri-base.json')['projectiles']
        self.assertEqual([(p['instance_name'], e['frame'], e['color_rgb24'])
                          for p in projectiles for e in p.get('frame_events', [])],
                         [('abcd', 17, 8978176), ('cbs1atm', 42, 4580164)])

    def test_ultimate_projectile_stops_moving_after_source_rename(self):
        projectile = next(p for p in read('data/actions/mayuri-base.json')['projectiles']
                          if p['instance_name'] == 'cbs1atm')
        self.assertEqual(projectile['initial_variables'], {'played': 0})
        self.assertEqual(projectile['local_motion_conditions'], [
            {'field': 'played', 'operator': '==', 'value': 0}])
        self.assertEqual(projectile['rename_frames'][0]['frame'], 40)
        self.assertEqual(projectile['rename_frames'][0]['local_writes'], [{'field': 'played', 'value': 1}])

    def test_projectile_named_jump_requires_source_label_resolution(self):
        from tools.importer.combat_projectile_parser import parse_projectile_motion

        source = next(s['source'] for s in read('scripts/fighter/mayuri.json')['scripts']
                      if s['path'] == 'DefineSprite_487/frame_395/PlaceObject2_220_28/CLIPACTIONRECORD onClipEvent(enterFrame).as')
        with self.assertRaisesRegex(ValueError, 'Missing projectile target label: hit'):
            parse_projectile_motion(source)
