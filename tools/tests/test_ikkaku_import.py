"""Ikkaku's controller aliases retain source movement and guard semantics."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_controller import compile_controller
from compile_ai_hit_state import compile_transfer
from compile_ai_context import compile_context


def read(path):
    return json.loads((ROOT / path).read_text())


class IkkakuImportTests(unittest.TestCase):
    def test_shared_sources_and_receiver_aliases(self):
        bundle = read('scripts/fighter/yijiao.json')
        scripts = {s['path']: s['source'] for s in bundle['scripts']}
        renji = {s['path']: s['source'] for s in read('scripts/fighter/Renji.json')['scripts']}
        for actual, expected in [(18, 16), (455, 717), (2, 2), (439, 2)]:
            self.assertEqual(scripts[f'DefineSprite_{actual}/frame_1/DoAction.as'],
                             renji[f'DefineSprite_{expected}/frame_1/DoAction.as'])
        code, _ = compile_transfer(bundle)
        self.assertEqual(code, compile_transfer(read('scripts/fighter/Renji.json'))[0])
        # Never merge genuinely different receiver implementations.
        alias = next(s for s in bundle['scripts'] if s['path'].startswith('DefineSprite_439/'))
        alias['source'] = alias['source'].replace('_parent.time = 0;', '_parent.time = 1;')
        self.assertNotEqual(alias['source'], scripts[alias['path']])
        with self.assertRaisesRegex(ValueError, 'found 2'):
            compile_transfer(bundle)

    def test_pure_motion_child_callbacks_preserve_source_lifetimes(self):
        bundle = read('scripts/fighter/yijiao.json')
        timeline = read('data/slices/yijiao-base.timeline.json')
        for player in (False, True):
            code, meta = compile_controller(bundle, 455, timeline, player=player)
            for start, end in [(483, 485), (486, 490), (491, 495)]:
                hook = next(h for h in meta['hooks'] if h['placement_frame'] == start)
                self.assertTrue(hook['child_controller'])
                self.assertEqual(hook['member_frames'], list(range(start, end + 1)))
            for call in ['child_267_moveX(10)', 'child_267_moveY(15)',
                         'child_267_moveX(2)', 'child_267_moveY(5)']:
                self.assertIn(call, code)
            self.assertFalse(meta['projectile_hooks'])

    def test_source_guard_and_super_events(self):
        model = read('data/actions/yijiao-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual(model, read('godot/generated/fighters/yijiao/combat.json'))
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(520, 'super_start'), (543, 'super_end'),
                          (579, 'super_start'), (604, 'super_end'),
                          (675, 'super_start'), (717, 'super_end')])
        self.assertEqual(model['on_defence_frames'][0]['frame'], 821)
        self.assertEqual(model['on_defence_frames'][0]['xgtype'], 2)
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']],
                         [(833, False), (846, True)])

    def test_wrapper_movement_stays_in_frame_statement_order(self):
        model = compile_context(read('scripts/fighter/yijiao.json'),
                                read('data/slices/yijiao-base.timeline.json'))
        for frame, expected in [('131', [('moveX', 5, 1), ('moveY', 5, 2)]),
                                ('545', [('moveX', 150, 1)])]:
            moves = [e for e in model['frame_calls'][frame] if e['op'] == 'wrapper_move']
            self.assertEqual([(e['axis'], e['pixels'], e['line']) for e in moves], expected)
        bundle = read('scripts/fighter/yijiao.json')
        wrapper = next(s for s in bundle['scripts'] if s['path'] == 'frame_1/DoAction.as')
        wrapper['source'] = wrapper['source'].replace('_X = _X + spd * scale_X;', '_X = _X + spd;')
        with self.assertRaisesRegex(ValueError, 'Unsupported wrapper movement'):
            compile_context(bundle, read('data/slices/yijiao-base.timeline.json'))


if __name__ == '__main__':
    unittest.main()
