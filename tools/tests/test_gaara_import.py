"""Source-backed Gaara frame dispatch and shared receiver invariants."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import conditional_frame_calls, root_opponent_warp


def read(path):
    return json.loads((ROOT / path).read_text())


class GaaraImportTests(unittest.TestCase):
    def test_shared_receiver_and_controller(self):
        sources = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('gaara', 'Renji')]
        for own, shared in ((2, 2), (20, 16), (673, 717)):
            self.assertEqual(sources[0][f'DefineSprite_{own}/frame_1/DoAction.as'],
                             sources[1][f'DefineSprite_{shared}/frame_1/DoAction.as'])

    def test_source_receiver_super_and_fallthrough(self):
        model = read('data/actions/gaara-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual(model, read('godot/generated/fighters/gaara/combat.json'))
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(486, 'super_start'), (498, 'super_end'), (611, 'super_start'),
                          (626, 'super_end'), (730, 'super_start'), (795, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']],
                         [(1093, False), (1106, True)])
        self.assertEqual(model['action_exits']['被打']['frame'], 1102)

    def test_source_visibility_branch_and_opponent_x_only(self):
        scripts = {s['path']: s['source'] for s in read('scripts/fighter/gaara.json')['scripts']}
        path = 'DefineSprite_673/frame_519/DoAction.as'
        calls = conditional_frame_calls(scripts[path], path, 519)
        self.assertEqual(calls, read('godot/generated/fighters/gaara/ai.json')['frame_calls']['519'])
        self.assertEqual(calls[0]['calls'], [{'op': 'opponent_visibility', 'value': False}])
        self.assertEqual(calls[0]['else_calls'][0]['label'], '必杀1')
        self.assertEqual(conditional_frame_calls(scripts[path].replace('play();', 'stop();'), path, 519), [])
        path = 'DefineSprite_673/frame_867/DoAction.as'
        warp = root_opponent_warp(scripts[path], path, 867)[0]
        self.assertTrue(warp['copy_x'])
        self.assertFalse(warp['copy_y'])

    def test_child_boom_label_and_follow_flags(self):
        calls = read('godot/generated/fighters/gaara/ai.json')['frame_calls']
        self.assertEqual(calls['535'][0]['target_frame'], 35)
        self.assertEqual(calls['535'][0]['character_id'], 349)
        for frame in (304, 305, 306, 307, 501):
            follow = calls[str(frame)][0]
            self.assertEqual(follow['op'], 'follow_clip')
            self.assertTrue(follow['place_x'])
            self.assertFalse(follow['place_y'])
            self.assertTrue(follow['front_only'])
