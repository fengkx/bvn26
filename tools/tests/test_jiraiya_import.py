"""Source invariants for Jiraiya's base form and shared combat chain."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class JiraiyaImportTests(unittest.TestCase):
    def test_shared_controller_receiver_and_body(self):
        sources = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('jiraiya', 'Renji')]
        for own, shared in ((11, 16), (2, 2), (342, 717)):
            self.assertEqual(sources[0][f'DefineSprite_{own}/frame_1/DoAction.as'],
                             sources[1][f'DefineSprite_{shared}/frame_1/DoAction.as'])

    def test_source_super_receiver_and_fallthrough_events(self):
        model = read('data/actions/jiraiya-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual(model, read('godot/generated/fighters/jiraiya/combat.json'))
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(611, 'super_start'), (637, 'super_end'),
                          (733, 'super_start'), (765, 'super_end'),
                          (820, 'super_start'), (868, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']],
                         [(1034, False), (1047, True)])
        self.assertEqual([(e['frame'], e['xgtype']) for e in model['on_defence_frames']],
                         [(1022, 2)])
        self.assertEqual(model['action_exits']['被打']['frame'], 1043)
        self.assertEqual([(e['from'], e['to'], e['frame']) for e in model['timeline_fallthroughs']],
                         [('跳招', '跳招1', 152), ('砍技2', '砍技20', 359), ('招3', '招31', 554)])
