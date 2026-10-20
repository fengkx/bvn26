"""Source invariants for Deidara's base timeline and clay projectile lifetimes."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class DidalaImportTests(unittest.TestCase):
    def test_shared_controller_receiver_and_body(self):
        sources = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('didala', 'Renji')]
        for own, shared in ((16, 16), (2, 2), (542, 717)):
            self.assertEqual(sources[0][f'DefineSprite_{own}/frame_1/DoAction.as'],
                             sources[1][f'DefineSprite_{shared}/frame_1/DoAction.as'])

    def test_source_super_and_receiver_frames(self):
        model = read('data/actions/didala-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual(model, read('godot/generated/fighters/didala/combat.json'))
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(477, 'super_start'), (496, 'super_end'),
                          (581, 'super_start'), (617, 'super_end'),
                          (707, 'super_start'), (769, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']],
                         [(904, False), (917, True)])
        self.assertEqual([(e['frame'], e['xgtype']) for e in model['on_defence_frames']],
                         [(892, 2)])
        self.assertEqual(model['action_exits']['被打']['frame'], 913)

    def test_projectiles_keep_source_motion_and_contact_renames(self):
        model = read('data/actions/didala-base.json')
        projectiles = model['projectiles']
        self.assertEqual([(p['character_id'], p['start_frame'], p['end_frame'])
                          for p in projectiles], [(84, 151, 167), (210, 356, 374), (281, 434, 452)])
        self.assertEqual([p['initial_variables'] for p in projectiles],
                         [{'movspeed': speed, 'played': 0} for speed in (15, 25, 20)])
        for projectile, attack in zip(projectiles, ('tzatm', 'zh1atm', 'zh3atm')):
            self.assertEqual(projectile['stop_frames'], [1, 12])
            self.assertEqual([(r['frame'], r['instance_name']) for r in projectile['rename_frames']],
                             [(5, attack), (9, 'bbb')])
            self.assertEqual(projectile['on_hit_goto_frame'], 5)
            self.assertEqual(projectile['child_stop_frames'], {'82': [12]})
        self.assertEqual(projectiles[0]['local_y_factor'], 1)
        self.assertEqual(projectiles[2]['local_y_factor'], -1)
        for directory in ('player_controller', 'ai_controller'):
            controller = read(f'godot/generated/fighters/didala/{directory}/controller.json')
            self.assertEqual(
                [hook['projectile']['child_stop_frames']
                 for hook in controller['projectile_hooks']],
                [{'82': [12]}] * 3,
            )
