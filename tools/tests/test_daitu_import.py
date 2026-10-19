"""Daitu base source contracts: delayed contact, visibility and receiver identity."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import conditional_frame_calls
from compile_ai_hit_state import compile_transfer


def read(path):
    return json.loads((ROOT / path).read_text())


class DaituImportTests(unittest.TestCase):
    def test_delayed_contact_is_not_recomputed_at_the_branch(self):
        context = read('godot/generated/fighters/daitu/ai.json')
        reset = context['frame_writes']['310']
        self.assertEqual([(e['field'], e['value']) for e in reset], [('kj2hit', False)])
        contact = context['frame_calls']['311'][0]
        self.assertEqual((contact['op'], contact['field_name'], contact['instance']),
                         ('frame_hit_test', 'kj2hit', 'zh30atm'))
        branch = context['frame_calls']['318'][0]
        self.assertEqual(branch['conditions'], [
            {'field': 'kj2hit', 'operator': 'eq', 'value': True},
            {'field': 'opponent_hp', 'operator': 'gt', 'value': 0},
            {'field': 'opponent_action', 'operator': 'eq', 'value': -1}])
        self.assertEqual(branch['calls'][0]['label'], '招32')
        source = next(s['source'] for s in read('scripts/fighter/daitu.json')['scripts']
                      if s['path'] == 'DefineSprite_458/frame_318/DoAction.as')
        self.assertFalse(conditional_frame_calls(source.replace(' && ', ' || ', 1), 'test', 318))

    def test_receiver_is_selected_from_actual_receive_callbacks(self):
        _, metadata = compile_transfer(read('scripts/fighter/daitu.json'))
        self.assertEqual(metadata['path'], 'DefineSprite_19/frame_1/DoAction.as')
        controller = read('godot/generated/fighters/daitu/player_controller/controller.json')
        self.assertEqual({h['receiver_symbol_id'] for h in controller['receiver_hooks']}, {19})

    def test_source_visibility_restore_and_super_pairs(self):
        context = read('godot/generated/fighters/daitu/ai.json')
        for frame in ('412', '773'):
            event = context['frame_calls'][frame][0]
            self.assertEqual((event['op'], event['value']), ('opponent_visibility', True))
        model = read('data/actions/daitu-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual(model, read('godot/generated/fighters/daitu/combat.json'))
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(530, 'super_start'), (547, 'super_end'),
                          (630, 'super_start'), (647, 'super_end'),
                          (802, 'super_start'), (916, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames'] if e['sprite_id'] == 458],
                         [(1064, False), (1077, True)])
        self.assertEqual(read('godot/generated/fighters/daitu/intro.json')['state_frames'],
                         {'1149': 1, '1151': 3, '1181': 2})
        self.assertEqual(read('godot/generated/main/character_selection/available.json')['fighters']['带土'], 'daitu')
        self.assertIn('daitu', read('services/matchmaking/src/catalog.json')['fighters'])
