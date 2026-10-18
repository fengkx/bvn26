"""Orochimaru's authored intermediate normal and shared receiver survive import."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from extract_fighter_slice import extract_slice


def read(path):
    return json.loads((ROOT / path).read_text())


class OrochimaruImportTests(unittest.TestCase):
    def test_shared_controller_receiver_and_body(self):
        sources = [{s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                   for name in ('orochimaru', 'Renji')]
        for symbol in (16, 2):
            path = f'DefineSprite_{symbol}/frame_1/DoAction.as'
            self.assertEqual(sources[0][path], sources[1][path])
        self.assertEqual(sources[0]['DefineSprite_541/frame_1/DoAction.as'],
                         sources[1]['DefineSprite_717/frame_1/DoAction.as'])

    def test_intermediate_normal_uses_source_order_and_placement_lifetime(self):
        model = read('data/actions/orochimaru-base.json')
        self.assertEqual(model['combo']['labels'], ['砍1', '砍11', '砍2', '砍3'])
        self.assertEqual([(t['from'], t['to'], t['start_frame'], t['end_frame'])
                          for t in model['combo']['transitions']],
                         [('砍1', '砍11', 211, 215), ('砍11', '砍2', 231, 236),
                          ('砍2', '砍3', 259, 265)])
        generated = extract_slice(ROOT, '大蛇丸')
        self.assertEqual(list(generated['actions']['ground_combo']), model['combo']['labels'])

    def test_source_super_and_receiver_events(self):
        model = read('data/actions/orochimaru-base.json')
        self.assertFalse(model['extracted_partial'])
        self.assertEqual(model, read('godot/generated/fighters/orochimaru/combat.json'))
        self.assertEqual([(e['frame'], e['op']) for e in model['super_events']],
                         [(540, 'super_start'), (588, 'super_end'),
                          (671, 'super_start'), (704, 'super_end'),
                          (779, 'super_start'), (849, 'super_end')])
        self.assertEqual([(e['frame'], e['flying']) for e in model['on_be_hit_frames']],
                         [(1103, False), (1116, True)])
        self.assertEqual(model['on_defence_frames'][0]['frame'], 1091)
        self.assertEqual(model['action_exits']['被打']['frame'], 1112)
