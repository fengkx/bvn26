"""Opening invariants from the locked AS2 scripts and compiled UI timelines."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class IntroSourceTests(unittest.TestCase):
    def test_character_completion_is_before_label_end(self):
        spec = read('godot/generated/main/intro/intro.json')
        for name, sprite, start, finish in [('minren', 764, 1099, 1160), ('yihu', 638, 822, 883)]:
            with self.subTest(name=name):
                source = {s['path']: s['source'] for s in read(f'scripts/fighter/{name}.json')['scripts']}
                self.assertIn('kcplayed = 2;', source[f'DefineSprite_{sprite}/frame_{finish}/DoAction.as'])
                self.assertIn('gotoAndStop("站立")', source[f'DefineSprite_{sprite}/frame_{finish}/DoAction.as'])
                actor = spec['fighters'][name]
                self.assertEqual(actor['action']['start_frame'], start)
                self.assertEqual(actor['state_frames'][str(finish)], 2)
                self.assertLess(finish, actor['action']['end_frame'])

    def test_ready_and_skip_have_distinct_unlock_frames(self):
        spec = read('godot/generated/main/intro/intro.json')
        self.assertEqual(spec['poll_ms'], 500)
        ready = spec['clips']['ready']
        wipe = spec['clips']['qjxg']
        self.assertTrue(ready['events']['127']['start_fight'])
        self.assertTrue(ready['events']['1']['stop'])
        self.assertEqual(wipe['labels']['skipintro'], 33)
        self.assertTrue(wipe['events']['36']['reset_fighters'])
        self.assertFalse(wipe['events']['36']['start_fight'])
        self.assertTrue(wipe['events']['40']['start_fight'])
        self.assertTrue(wipe['events']['40']['rewind'])

    def test_number_and_speech_segments_come_from_source(self):
        timeline = read('godot/generated/main/intro/ready/timeline.json')
        digits = next(d for d in timeline['definitions'] if d['character_id'] == 1875)
        self.assertEqual(digits['intro_round_offset'], 5)
        sound = {f['frame']: [e for e in f.get('events', []) if e['type'] == 'start_sound'] for f in timeline['frames']}
        self.assertEqual(sound[59][0]['out_point'], 50124)
        self.assertEqual(sound[92][0]['in_point'], 50627)
        self.assertEqual(sound[92][0]['out_point'], 92879)
        for clip in ['ready', 'qjxg']:
            folder = f'godot/generated/main/intro/{clip}'
            timeline = read(folder + '/timeline.json')
            for d in timeline['definitions']:
                if d['type'].startswith('DefineShape') and not d.get('bitmap_fills'):
                    self.assertTrue((ROOT / folder / f'shape-{d["character_id"]}.png').is_file())


if __name__ == '__main__':
    unittest.main()
