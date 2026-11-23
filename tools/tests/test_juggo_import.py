"""Juugo's source placements, callbacks and guard invariants."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_predicates import expression
from source_instance_key import instance_key


def read(path):
    return json.loads((ROOT / path).read_text())


class JuugoImportTests(unittest.TestCase):
    def test_receiver_matches_shared_source(self):
        bundles = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('juggo', 'Renji')]
        for own, shared in ((2, 2),):
            self.assertEqual(bundles[0][f'DefineSprite_{own}/frame_1/DoAction.as'],
                             bundles[1][f'DefineSprite_{shared}/frame_1/DoAction.as'])

    def test_foot_query_keeps_its_source_target(self):
        query = '_parent.kj10atm.hitTest(_root.game["p" + _parent.pn].mc.jiao)'
        self.assertEqual(expression(query, set()), 'body_hit("kj10atm", "jiao")')

    def test_source_super_and_receiver_frames(self):
        model = read('data/actions/juggo-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(573, 'super_start'), (611, 'super_end'), (719, 'super_start'),
                          (755, 'super_end'), (830, 'super_start'), (876, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']],
                         [(1142, False), (1155, True)])
        self.assertEqual(model['action_exits']['被打']['frame'], 1151)

    def test_camera_focus_follows_body_frame_writes(self):
        for fighter, start, end in [('juggo', 918, 1000), ('lee', 643, 673)]:
            calls = read(f'godot/generated/fighters/{fighter}/ai.json')['frame_calls']
            for frame, target in [(start, 'caster'), (end, 'all')]:
                self.assertEqual([event['target'] for event in calls[str(frame)]
                                  if event['op'] == 'camera_focus'], [target])

    def test_child_callbacks_and_unnamed_projectile_identity(self):
        model = read('godot/generated/fighters/juggo/player_controller/controller.json')
        ops = {h['placement_frame']: h for h in model['hooks'] if 'source_child_operation' in h}
        self.assertEqual(ops[315]['target_label'], '砍技21')
        self.assertEqual(ops[890]['source_child_operation'], 'opponent_follow')
        timeline = read('data/slices/juggo-base.timeline.json')
        placement = next(p for p in timeline['frames'][369]['display_list'] if p['placed_frame'] == 370)
        self.assertNotIn('name', placement)
        key = instance_key(placement)
        self.assertTrue(any(h['projectile']['instance_name'] == key for h in model['projectile_hooks']))
        self.assertNotEqual(key, instance_key({**placement, 'placed_frame': 374}))
