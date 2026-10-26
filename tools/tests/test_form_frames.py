import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_form_frames import compile_form_frame
from compile_ai_context import parent_initial_values, form_initialization
from compile_ai_body import compile_player_body


class FormFrameTests(unittest.TestCase):
    def bundle(self, name):
        return json.loads((ROOT / 'scripts/fighter' / (name + '.json')).read_text())

    def compile_frame(self, name, sprite, frame):
        bundle = self.bundle(name)
        path = f'DefineSprite_{sprite}/frame_{frame}/DoAction.as'
        source = next(s['source'] for s in bundle['scripts'] if s['path'] == path)
        result = compile_form_frame(bundle, source, path, frame, 1)
        self.assertEqual(result[0]['source_sha256'], hashlib.sha256(source.encode()).hexdigest())
        return result[0]

    def test_source_parent_gotos_resolve_exact_loads(self):
        for name, sprite, frame, target in [('daitu', 458, 1309, 1138),
                ('minren', 764, 1382, 1293), ('Sasuke', 603, 1232, 1019),
                ('yihu', 638, 1055, 1180)]:
            with self.subTest(name=name):
                event = self.compile_frame(name, sprite, frame)
                self.assertEqual(event['op'], 'parent_form_goto')
                self.assertEqual(event['replacement']['target_body_sprite'], target)
                self.assertFalse(event['play'])

    def test_wankai_keeps_body_ownership(self):
        event = self.compile_frame('daitu', 458, 1307)
        self.assertEqual((event['op'], event['method']), ('body_form_call', 'wankai'))
        self.assertEqual(event['replacement']['target_parent_frame'], 2)

    def test_transfer_and_interval_are_complete_blocks(self):
        for name, sprite, frames in [('minren', 764, [1379, 1380, 1381]),
                                    ('Sasuke', 603, [1228, 1229, 1230])]:
            events = [self.compile_frame(name, sprite, frame) for frame in frames]
            self.assertEqual([e['op'] for e in events],
                             ['form_prepare_slot', 'form_prepare_slot', 'form_start_interval'])
            self.assertEqual({e['slot'] for e in events[:2]}, {'p1', 'p2'})
            self.assertEqual(events[-1]['delay_ms'], 1000)

    def test_interval_block_retains_trailing_parent_flag_in_order(self):
        for name, sprite, frame in [('minren', 764, 1381), ('Sasuke', 603, 1230)]:
            bundle = self.bundle(name)
            path = f'DefineSprite_{sprite}/frame_{frame}/DoAction.as'
            source = next(s['source'] for s in bundle['scripts'] if s['path'] == path)
            events = compile_form_frame(bundle, source, path, frame, 1)
            self.assertEqual([e['op'] for e in events], ['form_start_interval', 'parent_frame_field'])
            self.assertEqual((events[1]['field_name'], events[1]['value']), ('万解', True))

    def test_extra_statement_or_expression_is_never_stripped(self):
        bundle = self.bundle('daitu')
        for source in ['wankai(); unknown();', '_parent.gotoAndStop(1 + 1);',
                       'if (ready) { wankai(); }', 'setInterval(feixue, 999);']:
            with self.subTest(source=source), self.assertRaisesRegex(
                    ValueError, r'game/fighter/daitu.swf:DefineSprite_458/frame_1307.*unsupported'):
                compile_form_frame(bundle, source, 'DefineSprite_458/frame_1307', 1307, 1)

    def test_parent_flag_comes_from_source_not_a_default(self):
        bundle = self.bundle('daitu')
        self.assertEqual(parent_initial_values(bundle, {}, form_replacement=True), {'万解': False})
        changed = copy.deepcopy(bundle)
        root = next(s for s in changed['scripts'] if s['path'] == 'frame_1/DoAction.as')
        root['source'] = root['source'].replace('var 万解 = false;', 'var 万解 = missing;')
        with self.assertRaisesRegex(ValueError, 'frame_1/DoAction.as.*initializer: 万解'):
            parent_initial_values(changed, {}, form_replacement=True)

    def test_parent_play_rejects_before_runtime(self):
        with self.assertRaisesRegex(ValueError, 'fixture/frame_9.*parent timeline clock'):
            compile_form_frame(self.bundle('daitu'), '_parent.gotoAndPlay(2);',
                               'fixture/frame_9', 9, 1)

    def test_initialization_requires_source_order_and_visibility(self):
        source = next(s['source'] for s in self.bundle('daitu')['scripts']
                      if s['path'] == 'DefineSprite_1138/frame_1/DoAction.as')
        self.assertTrue(form_initialization(source, 'daitu.swf:1138/1')['wrapper_visible'])
        for changed in [source.replace('_parent._visible = true;', ''),
                        source.replace('doWanKai();', 'unknownInit();')]:
            with self.assertRaisesRegex(ValueError, 'daitu.swf:1138/1.*initialization/order'):
                form_initialization(changed, 'daitu.swf:1138/1')

    def test_packaged_player_body_preserves_hurt_placement_callbacks(self):
        base = ROOT / 'godot/generated/fighters/daitu'
        timeline = json.loads((base / 'timeline.json').read_text())
        _, metadata = compile_player_body(self.bundle('daitu'), 458, timeline, form_helpers=True)
        expected = json.loads((base / 'player_controller/body.json').read_text())['hurt_hooks']
        self.assertEqual(metadata['hurt_hooks'], expected)
        self.assertEqual(len(metadata['hurt_hooks']), 3)
