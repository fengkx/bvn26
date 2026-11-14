"""Retained Killer Bee placement and facing invariants."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from build_combat_model import parse_body_warp, parse_clip_timeline
from compile_ai_controller import compile_controller


class QilabiImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / 'scripts/fighter/qilabi.json').read_text())
        cls.timeline = json.loads((ROOT / 'data/slices/qilabi-base.timeline.json').read_text())
        cls.scripts = {s['path']: s['source'] for s in cls.bundle['scripts']}

    def test_super_reverses_facing_and_warps_only_x(self):
        source = self.scripts['DefineSprite_766/frame_556/DoAction.as']
        warp = parse_body_warp(source)
        self.assertEqual(warp, {
            'op': 'warp_to_opponent', 'place_x': True,
            'xscale_lt_0': {'set_xscale': 100.0, 'set_scale_x': 1, 'x_pixels': -80.0},
            'xscale_gt_0': {'set_xscale': -100.0, 'set_scale_x': -1, 'x_pixels': 80.0},
        })

    def test_placement_function_and_deceleration_are_compiled(self):
        code, metadata = compile_controller(self.bundle, 766, self.timeline, player=True)
        # The load callback owns this speed, so every newly placed instance
        # starts at 15; the generated instance field also enters checkpoints.
        self.assertIn('var frame_289_depth_35_spd: Variant = 15', code)
        self.assertIn('frame_289_depth_35_spd = number(frame_289_depth_35_spd) - 1', code)
        self.assertIn('func frame_270_depth_30_attack(fn: Variant = null)', code)
        self.assertIn('frame_270_depth_30_attack("上必杀")', code)
        self.assertIn('adapter.effect("updateDirect")', code)
        hook = next(h for h in metadata['hooks'] if h['placement_frame'] == 289)
        self.assertEqual(hook['depth'], 35)
        self.assertEqual(hook['member_frames'][0], 289)

    def test_unresolved_placement_call_is_rejected(self):
        bundle = json.loads(json.dumps(self.bundle))
        bundle['scripts'] = [s for s in bundle['scripts'] if s['path'] !=
                            'DefineSprite_766/frame_270/PlaceObject2_22_30/CLIPACTIONRECORD onClipEvent(load).as']
        with self.assertRaisesRegex(ValueError, 'Unsupported call.*attack'):
            compile_controller(bundle, 766, self.timeline, player=True)

    def test_upper_projectile_starts_stopped_with_only_authored_local(self):
        clip = parse_clip_timeline(self.bundle, 256)
        self.assertEqual(clip['initial_variables'], {'played': 0})
        self.assertEqual(clip['stop_frames'], [1, 12])
        self.assertEqual([(event['frame'], event['instance_name']) for event in clip['rename_frames']],
                         [(6, 'zh3atm'), (9, 'aaa')])


if __name__ == '__main__':
    unittest.main()
