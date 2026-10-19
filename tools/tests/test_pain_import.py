"""Source invariants for Pain's base form and shared combat chain."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class PainImportTests(unittest.TestCase):
    def test_shared_controller_receiver_and_body(self):
        sources = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('pain', 'Renji')]
        for own, shared in ((18, 16), (5, 2), (573, 717)):
            self.assertEqual(sources[0][f'DefineSprite_{own}/frame_1/DoAction.as'],
                             sources[1][f'DefineSprite_{shared}/frame_1/DoAction.as'])

    def test_source_super_receiver_and_fallthrough_events(self):
        model = read('data/actions/pain-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual(model, read('godot/generated/fighters/pain/combat.json'))
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(603, 'super_start'), (640, 'super_end'),
                          (745, 'super_start'), (769, 'super_end'),
                          (844, 'super_start'), (856, 'super_end'),
                          (908, 'super_start'), (941, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']],
                         [(1182, False), (1195, True)])
        self.assertEqual([(e['frame'], e['xgtype']) for e in model['on_defence_frames']],
                         [(1170, 2)])
        self.assertEqual(model['action_exits']['被打']['frame'], 1191)
        self.assertEqual([(e['from'], e['to'], e['frame']) for e in model['timeline_fallthroughs']],
                         [('砍技2', '砍技21', 427), ('砍技21', '砍技22', 431)])

    def test_attraction_callback_preserves_source_lifetime_and_scalars(self):
        import sys
        sys.path.insert(0, str(ROOT / 'tools/importer'))
        from compile_ai_controller import compile_body
        source = next(s for s in read('scripts/fighter/pain.json')['scripts']
                      if '/frame_943/PlaceObject2_18_38/' in s['path'])
        body = source['source'].replace('\r\n', '\n').split('\n', 1)[1].rsplit('}', 1)[0]
        code = compile_body('attraction', '', body)
        self.assertIn('write_value("opponent_x"', code)
        self.assertIn('write_value("opponent_y"', code)
        self.assertIn('250', code)
        hooks = read('godot/generated/fighters/pain/player_controller/controller.json')['hooks']
        hook = next(h for h in hooks if h['placement_frame'] == 943)
        self.assertEqual(hook['member_frames'], list(range(943, 1054)))
        self.assertEqual(hook['depth'], 38)
        with self.assertRaisesRegex(ValueError, 'alias reassigned'):
            compile_body('invalid', '', 'var target = _parent._parent;\ntarget = 0;')

    def test_warp_keeps_authored_logical_facing_separate_from_display_scale(self):
        import sys
        sys.path.insert(0, str(ROOT / 'tools/importer'))
        from build_combat_model import parse_body_warp
        source = next(s['source'] for s in read('scripts/fighter/pain.json')['scripts']
                      if s['path'] == 'DefineSprite_573/frame_423/DoAction.as')
        self.assertEqual(parse_body_warp(source), {
            'op': 'warp_to_opponent', 'place_x': True, 'place_y': True,
            'xscale_lt_0': {'set_xscale': 100.0, 'x_pixels': -30.0, 'set_scale_x': 1},
            'xscale_gt_0': {'set_xscale': -100.0, 'x_pixels': 30.0, 'set_scale_x': -1},
        })
        # A visual scale write alone must never invent a logical-facing write.
        without_facing = source.replace('   _parent.scale_X = 1;\r\n', '').replace(
            '   _parent.scale_X = -1;\r\n', '')
        warp = parse_body_warp(without_facing)
        self.assertNotIn('set_scale_x', warp['xscale_lt_0'])
        self.assertNotIn('set_scale_x', warp['xscale_gt_0'])
