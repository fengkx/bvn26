"""New fighter imports must retain their own controller and source semantics."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_predicates import controller_script
from compile_ai_controller import compile_controller
from extract_fighter_slice import extract_slice
from compile_hit_receive import compile_hit_fx, _clip_events_for_prefix, compile_wall_hit_near
from compile_ai_context import compile_context


class CharacterImportTests(unittest.TestCase):
    def test_wall_hit_near_retains_source_thresholds_and_rejects_unknown_branch(self):
        for name, sprite in [('minren', 764), ('yihu', 638), ('rifagu', 638)]:
            bundle = json.loads((ROOT / f'scripts/fighter/{name}.json').read_text())
            rule = compile_wall_hit_near(bundle, sprite)
            self.assertEqual((rule['distance'], rule['side_split_x']), (100, 500))
            script = next(s for s in bundle['scripts'] if s['path'] == rule['source_path'])
            script['source'] = script['source'].replace('if(_parent.hitWall)', 'if(true)')
            with self.assertRaisesRegex(ValueError, 'Uncompiled wall hitNear'):
                compile_wall_hit_near(bundle, sprite)

    def test_guard_callback_does_not_invent_a_parent_receiver(self):
        for fighter in ['rifagu', 'yihu']:
            bundle = json.loads((ROOT / f'scripts/fighter/{fighter}.json').read_text())
            timeline = json.loads((ROOT / f'data/slices/{fighter}-base.timeline.json').read_text())
            code, metadata = compile_controller(bundle, timeline['sprite_id'], timeline, player=True)
            if fighter == 'rifagu':
                self.assertNotIn('adapter.body_call("fangyux"', code)
                self.assertEqual([site['name'] for site in metadata['unbound_call_sites']], ['fangyux'])
            else:
                self.assertIn('adapter.body_call("fangyux", [])', code)
                self.assertFalse(metadata.get('unbound_call_sites'))

    def test_shared_guard_switch_retains_every_grouped_case(self):
        source = json.loads((ROOT / 'scripts/main.json').read_text())
        fx = compile_hit_fx(source)
        for table in ['bdfyxg', 'bdfyxg2']:
            for strength in [5, 7, 8, 9, 10]:
                self.assertEqual(fx[table][strength], 'XG_mffyx')
        self.assertEqual(fx['bdfyxg2'][2], 'XG_fyq')
        self.assertEqual(fx['bdfyxg2'][6], 'XG_fyqx')

    def test_original_root_shake_assignments_keep_operator_and_both_axes(self):
        main = json.loads((ROOT / 'scripts/main.json').read_text())
        events = _clip_events_for_prefix(main, 'DefineSprite_358_XG_ice')
        writes = [e for e in events if e['frame'] == 13 and e['op'] == 'shake_root']
        self.assertEqual([(e['axis'], e['operator'], e['pixels']) for e in writes],
                         [('y', '=', 0), ('x', '=', 0)])
        bundle = json.loads((ROOT / 'scripts/fighter/rifagu.json').read_text())
        timeline = json.loads((ROOT / 'data/slices/rifagu-base.timeline.json').read_text())
        context = compile_context(bundle, timeline)
        for frame, operator in [(254, '-='), (255, '+='), (256, '-='), (257, '+=')]:
            event = context['frame_calls'][str(frame)][0]
            self.assertEqual((event['op'], event['axis'], event['operator'], event['pixels']),
                             ('root_position', 'y', operator, 2))

    def test_controller_is_placed_in_requested_form(self):
        for name, symbol in [('minren', 16), ('yihu', 16), ('rifagu', 14)]:
            with self.subTest(fighter=name):
                bundle = json.loads((ROOT / f'scripts/fighter/{name}.json').read_text())
                self.assertEqual(controller_script(bundle)['path'], f'DefineSprite_{symbol}/frame_1/DoAction.as')

    def test_rifagu_uses_original_base_timeline_and_attack_tables(self):
        result = extract_slice(ROOT, '日番谷')
        self.assertEqual(result['source']['timeline_symbol_id'], 638)
        self.assertEqual(result['actions']['special']['必杀']['start_frame'], 497)
        self.assertEqual(set(result['hit_parameters']['attacks_by_form']), {'1', '2'})

    def test_rifagu_projectile_load_and_diagonal_motion(self):
        bundle = json.loads((ROOT / 'scripts/fighter/rifagu.json').read_text())
        timeline = json.loads((ROOT / 'data/slices/rifagu-base.timeline.json').read_text())
        _, metadata = compile_controller(bundle, 638, timeline, player=True)
        hook = next(h for h in metadata['projectile_hooks'] if h['placement_frame'] == 154)
        self.assertEqual(hook['projectile']['initial_speed_factor'], 1)
        self.assertEqual(hook['projectile']['local_x_factor'], 1)
        self.assertEqual(hook['projectile']['local_y_factor'], 1)
        self.assertEqual(hook['projectile']['on_hit_goto_frame'], 5)


if __name__ == '__main__':
    unittest.main()
