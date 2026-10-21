"""Aizen source scope, mask contours, receiver and warp invariants."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from combat_projectile_parser import parse_projectile_motion
from build_combat_model import parse_body_warp


def read(path):
    return json.loads((ROOT / path).read_text())


class LanranImportTests(unittest.TestCase):
    def test_shared_receiver_and_body(self):
        sources = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('lanran', 'Renji')]
        for own, shared in ((2, 2), (640, 717)):
            self.assertEqual(sources[0][f'DefineSprite_{own}/frame_1/DoAction.as'],
                             sources[1][f'DefineSprite_{shared}/frame_1/DoAction.as'])

    def test_controller_container_writes_are_not_projectile_parent_writes(self):
        scripts = read('scripts/fighter/lanran.json')['scripts']
        for frame in (14, 747):
            script = next(s for s in scripts if s['path'].startswith(f'DefineSprite_640/frame_{frame}/PlaceObject2_15_'))
            self.assertIsNone(parse_projectile_motion(script['source']))
        with self.assertRaisesRegex(ValueError, 'not guarded'):
            parse_projectile_motion('onClipEvent(enterFrame){ _parent.Cbshit = true; }')

    def test_source_counter_writes_logical_facing_before_display_scale(self):
        scripts = read('scripts/fighter/lanran.json')['scripts']
        model = read('data/actions/lanran-base.json')
        for frame in (513, 1853):
            source = next(s['source'] for s in scripts if s['path'] == f'DefineSprite_640/frame_{frame}/DoAction.as')
            warp = parse_body_warp(source)
            self.assertEqual(warp['xscale_lt_0'], {'set_xscale': 100.0, 'x_pixels': -50.0, 'set_scale_x': 1})
            self.assertEqual(warp['xscale_gt_0'], {'set_xscale': -100.0, 'x_pixels': 50.0, 'set_scale_x': -1})
            compiled = next(e for e in model['body_warps'] if e['frame'] == frame)
            self.assertEqual(compiled['xscale_lt_0'], warp['xscale_lt_0'])

    def test_mask_uses_fill_edges_without_authored_stroke_expansion(self):
        timeline = read('data/slices/lanran-base.timeline.json')
        mask = next(d for d in timeline['definitions'] if d['character_id'] == 33)
        self.assertEqual(mask['mask_polygon'], [[51.95, -10.75], [51.95, 60.5], [11.95, 60.5], [11.95, -10.75]])
        self.assertEqual(mask['shape_bounds_twips']['Xmin'], 229)
        self.assertNotEqual(mask['mask_polygon'][2][0], 229 / 20)

    def test_source_super_and_receiver_frames(self):
        model = read('data/actions/lanran-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual(model, read('godot/generated/fighters/lanran/combat.json'))
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(806, 'super_start'), (842, 'super_end'), (918, 'super_start'), (955, 'super_end'),
                          (1148, 'super_start'), (1166, 'super_end'), (1219, 'super_start'), (1259, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']], [(1533, False), (1546, True)])
        self.assertEqual([(e['frame'], e['xgtype']) for e in model['on_defence_frames']], [(1521, 1), (1801, 1)])
        self.assertEqual(model['action_exits']['被打']['frame'], 1542)
