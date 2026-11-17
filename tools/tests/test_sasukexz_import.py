"""Source invariants for Susanoo Sasuke; not original-player acceptance."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from build_combat_model import parse_body_warp
from compile_ai_context import compile_context
from extract_fighter_slice import extract_slice
from frame_call_guard import validate_cached_frame_calls


class SasukexzImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / 'scripts/fighter/sasukexz.json').read_text())
        cls.scripts = {item['path']: item['source'] for item in cls.bundle['scripts']}
        cls.directory = ROOT / 'godot/generated/fighters/sasukexz'
        cls.timeline = json.loads((cls.directory / 'timeline.json').read_text())
        cls.context = json.loads((cls.directory / 'ai.json').read_text())

    def test_source_selected_standalone_body(self):
        fighter = extract_slice(ROOT, '佐助须佐', allow_forms=True)
        self.assertEqual(fighter['form_frame'], 1)
        self.assertEqual(fighter['source']['timeline_symbol_id'], 727)
        self.assertEqual(fighter['source']['swf_path'], 'game/fighter/sasukexz.swf')
        labels = {label for frame in self.timeline['frames'] for label in frame['labels']}
        self.assertNotIn('万解', labels)

    def test_upper_attack_reverses_and_copies_both_axes(self):
        source = self.scripts['DefineSprite_727/frame_493/DoAction.as']
        self.assertEqual(parse_body_warp(source), {
            'op': 'warp_to_opponent', 'place_x': True, 'place_y': True,
            'xscale_lt_0': {'set_xscale': 100.0, 'x_pixels': -50.0},
            'xscale_gt_0': {'set_xscale': -100.0, 'x_pixels': 50.0},
        })

    def test_conditional_followup_and_visibility_are_retained(self):
        self.assertIn('mc.hp > 0 && _root.game["p" + pn].mc.动作 == -1',
                      self.scripts['DefineSprite_727/frame_624/DoAction.as'])
        self.assertIn('gotoAndStop("招21")', self.scripts['DefineSprite_727/frame_624/DoAction.as'])
        for frame, value in ((638, 'false'), (679, 'true')):
            self.assertEqual(self.scripts[f'DefineSprite_727/frame_{frame}/DoAction.as'].strip(),
                             f'_root.game["p" + pn]._visible = {value};')
            self.assertTrue(self.context['frame_calls'][str(frame)])

    def test_fresh_strict_compile_and_every_call_guard(self):
        compiled = compile_context(self.bundle, self.timeline)
        self.assertEqual(compiled, self.context)
        validate_cached_frame_calls(self.timeline, self.context, directory=self.directory)
        for frame, calls in self.context['frame_calls'].items():
            for index in range(len(calls)):
                with self.subTest(frame=frame, call=index):
                    changed = copy.deepcopy(self.context)
                    del changed['frame_calls'][frame][index]
                    with self.assertRaisesRegex(ValueError, 'dropped/changed cached frame calls'):
                        validate_cached_frame_calls(self.timeline, changed, directory=self.directory)


if __name__ == '__main__':
    unittest.main()
