"""Kenpachi source receiver, frame branches and helper invariants."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from compile_ai_context import conditional_frame_calls


def read(path):
    return json.loads((ROOT / path).read_text())


class JianbaImportTests(unittest.TestCase):
    def test_shared_receiver_controller_and_body(self):
        sources = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('jianba', 'Renji')]
        for own, shared in ((2, 2), (13, 16), (514, 717)):
            self.assertEqual(sources[0][f'DefineSprite_{own}/frame_1/DoAction.as'],
                             sources[1][f'DefineSprite_{shared}/frame_1/DoAction.as'])

    def test_source_super_and_receiver_frames(self):
        model = read('data/actions/jianba-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual(model, read('godot/generated/fighters/jianba/combat.json'))
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(535, 'super_start'), (554, 'super_end'), (595, 'super_start'),
                          (611, 'super_end'), (708, 'super_start'), (752, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']], [(1048, False), (1061, True)])
        self.assertEqual([(e['frame'], e['xgtype']) for e in model['on_defence_frames']], [(1036, 1)])
        self.assertEqual(model['action_exits']['被打']['frame'], 1057)
        self.assertEqual([(e['frame'], e['from'], e['to']) for e in model['timeline_fallthroughs']],
                         [(152, '跳招', '跳招20'), (306, '砍技2', '砍技21')])

    def test_ultimate_requires_live_target_then_hurt_or_contact(self):
        path = 'DefineSprite_514/frame_767/DoAction.as'
        source = next(s['source'] for s in read('scripts/fighter/jianba.json')['scripts'] if s['path'] == path)
        calls = conditional_frame_calls(source, path, 767)
        self.assertEqual(calls, read('godot/generated/fighters/jianba/ai.json')['frame_calls']['767'])
        self.assertEqual(calls[0]['conditions'], [{'field': 'opponent_hp', 'operator': 'gt', 'value': 0}])
        self.assertEqual(calls[0]['alternatives'], [
            {'field': 'opponent_action', 'operator': 'eq', 'value': -1},
            {'instance': 'cbs0atm', 'operator': 'eq', 'value': True}])
        self.assertEqual(calls[0]['calls'][0]['label'], '超必杀1')
        self.assertEqual(conditional_frame_calls(source.replace('play();', 'stop();', 1), path, 767), [])
        # A different destination in the contact branch must not be silently collapsed.
        self.assertEqual(conditional_frame_calls(source.replace('超必杀1', 'other', 1), path, 767), [])

    def test_helper_packet_and_source_pause(self):
        model = read('data/actions/jianba-helper.json')
        self.assertEqual(model, read('godot/generated/helpers/jianba/combat.json'))
        self.assertEqual(model['attacks']['atm1']['damage'], 200)
        self.assertEqual([(e['frame'], e['op']) for e in model['presentation_events']],
                         [(2, 'effect'), (16, 'super_start'), (61, 'super_end'), (104, 'effect')])
