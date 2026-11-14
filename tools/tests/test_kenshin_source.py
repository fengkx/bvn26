"""Source invariants for Kenshin's three authored BODY placements."""
import json
from pathlib import Path
import sys
import unittest
import ast

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from extract_fighter_slice import extract_slice
from compile_ai_context import conditional_frame_calls, inline_frame_function, FUNCTION
from parent_form_requirements import parent_form_requirement
from compile_ai_predicates import normalize_ternary
from compile_ai_controller import compile_body
from build_combat_model import parse_body_warp


class KenshinSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / 'scripts/fighter/Kenshin.json').read_text())
        cls.scripts = {item['path']: item['source'] for item in cls.bundle['scripts']}

    def test_body_placement_ignores_presentation_sibling(self):
        for frame, sprite in [(1, 643), (2, 1473), (3, 2506)]:
            fighter = extract_slice(ROOT, '剑心', allow_forms=True, parent_frame=frame)
            self.assertEqual(fighter['source']['timeline_symbol_id'], sprite)
            self.assertEqual(parent_form_requirement(self.bundle, frame, 'test')['target_body_sprite'], sprite)

    def test_healing_keeps_unconditional_source_arithmetic(self):
        path = 'DefineSprite_2506/frame_600/DoAction.as'
        self.assertEqual(self.scripts[path].strip(), 'hp += 350;')
        calls = conditional_frame_calls(self.scripts[path], path, 600)
        self.assertEqual(calls, [{'op': 'frame_field', 'path': path, 'line': 1, 'frame': 600,
                                 'field_name': 'hp', 'operator': '+=', 'value': 350}])
        self.assertEqual(conditional_frame_calls('hp += 350;\nunknown();', path, 600), [])

    def test_transformation_end_preserves_guard_and_write_order(self):
        for sprite in (1473, 2506):
            source = self.scripts[f'DefineSprite_{sprite}/frame_1/DoAction.as']
            function = next(m[0] for m in FUNCTION.finditer(source) if m[1] == 'wankai_end')
            calls = inline_frame_function(function, 'source', 1)
            self.assertEqual(calls[0]['field_name'], '万解')
            self.assertEqual([c['op'] for c in calls[0]['calls']],
                             ['super_end', 'frame_field', 'parent_frame_field'])
            self.assertFalse(calls[0]['calls'][-1]['value'])
            with self.assertRaises(ValueError):
                inline_frame_function(function.replace('bs = 0;', 'unknown();'), 'source', 1)

    def test_replacement_calls_are_retained(self):
        for sprite, frame in [(643, 1148), (1473, 1503)]:
            self.assertEqual(self.scripts[f'DefineSprite_{sprite}/frame_{frame}/DoAction.as'].strip(), 'wankai();')

    def test_facing_ternary_keeps_multiplier_outside_condition(self):
        for facing, expected in [(-100, -8), (0, -8), (100, 8)]:
            tree = ast.parse(normalize_ternary('8 * (facing <= 0 ? -1 : 1)'), mode='eval')
            self.assertIsInstance(tree.body, ast.BinOp)
            self.assertEqual(eval(compile(tree, '<test>', 'eval'), {'facing': facing}), expected)
        self.assertEqual(normalize_ternary('"literal?:"'), '"literal?:"')

    def test_child_shadow_preserves_missing_blue_channel(self):
        path = 'DefineSprite_2506/frame_681/PlaceObject2_2274_43/CLIPACTIONRECORD onClipEvent(enterFrame).as'
        source = self.scripts[path].split('\n', 1)[1].rsplit('}', 1)[0]
        code = compile_body('source_shadow', '', source)
        self.assertIn('adapter.effect_with_args("showdow", [{"R": 255, "G": 0}])', code)
        with self.assertRaises(ValueError):
            compile_body('bad_shadow', '', '_parent._parent.showdow({R:255,R:0});')

    def test_super_warp_combines_authored_width_and_pixel_offset(self):
        source = self.scripts['DefineSprite_643/frame_552/DoAction.as']
        warp = parse_body_warp(source)
        self.assertEqual(warp['xscale_gt_0'], {'x_bdmn_width': 1.0, 'x_pixels': 100.0})
        self.assertEqual(warp['xscale_lt_0'], {'x_bdmn_width': -1.0, 'x_pixels': -100.0})
        self.assertNotIn('place_y', warp)


if __name__ == '__main__':
    unittest.main()
