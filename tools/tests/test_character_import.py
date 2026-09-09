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


class CharacterImportTests(unittest.TestCase):
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
