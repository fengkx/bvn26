"""Helper timing invariants retained from the original SWF and scripts."""
import json
import unittest
import tempfile
from pathlib import Path

from tools.importer.build_helper_model import (
    build_model,
    find_unconditional_root_stop_line,
    has_unconditional_root_stop,
)
from tools.probes.check_helper_timing import compare

ROOT = Path(__file__).resolve().parents[2]


class HelperTimingTests(unittest.TestCase):
    def test_root_stop_is_source_level_and_not_nested_control_flow(self):
        self.assertTrue(has_unconditional_root_stop('_root.fzccXg(this);\n' 'gotoAndStop(1);'))
        self.assertTrue(has_unconditional_root_stop('if (miss) {\n}\n' 'gotoAndStop ( 1 );'))
        self.assertFalse(has_unconditional_root_stop('if (hit) { gotoAndStop(1); }'))
        self.assertFalse(has_unconditional_root_stop('function park() { gotoAndStop(1); }'))
        self.assertFalse(has_unconditional_root_stop('// gotoAndStop(1);'))
        self.assertEqual(find_unconditional_root_stop_line('/* park */\n' 'gotoAndStop(1); // source stop'), 2)

    def test_you_miss_root_stop_is_compiled_with_source_provenance(self):
        model = build_model(
            ROOT / 'scripts/fighter/fz/you.json',
            Path('game/fighter/fz/you.swf'),
            '鼬',
            ROOT / 'data/slices/you-helper.timeline.json',
        )
        self.assertEqual(model['hide_frames'], [76])
        self.assertEqual(model['hide_frame_events'], [{
            'frame': 76,
            'op': 'root_goto_and_stop',
            'target_frame': 1,
            'source_path': 'frame_76/DoAction.as',
            'source_line': 2,
            'source_sha256': model['hide_frame_events'][0]['source_sha256'],
        }])
        self.assertEqual(model['hide_frame_events'][0]['source_sha256'],
                         next(item['source_sha256'] for item in model['indexed_source_events']
                              if item['path'] == 'frame_76/DoAction.as'))

    def test_gaara_terminal_stop_and_root_lifetime(self):
        model = build_model(ROOT / 'scripts/fighter/fz/woailuo.json',
                            ROOT / 'game/fighter/fz/woailuo.swf', '我爱罗')
        self.assertEqual((model['start_frame'], model['end_frame']), (2, 85))
        self.assertEqual([(x['sprite_id'], x['frame']) for x in model['nested_stops']], [(48, 33)])
        self.assertEqual(model['hide_frames'], [])
        self.assertEqual(model['hide_frame_events'], [])
        timeline = json.loads((ROOT / 'godot/generated/helpers/woailuo/timeline.json').read_text())
        sand = next(x for x in timeline['definitions'] if x['character_id'] == 48)
        self.assertEqual(sand['display_list_frames'][32], [])
        placements = [(f['frame'], p['placed_frame']) for f in timeline['frames']
                      for p in f['display_list'] if p.get('name') == 'atm1']
        self.assertEqual(placements, [(frame, 44) for frame in range(44, 86)])

    def test_receiver_can_requery_sand_after_replacement(self):
        bundle = json.loads((ROOT / 'scripts/fighter/yihu.json').read_text())
        scripts = {s['path']: s['source'].replace('\r\n', '\n').strip() for s in bundle['scripts']}
        self.assertEqual(scripts['DefineSprite_638/frame_739/DoAction.as'], 'onBeHit();')
        self.assertEqual(scripts['DefineSprite_638/frame_741/PlaceObject2_2_28/CLIPACTIONRECORD onClipEvent(enterFrame).as'],
                         'onClipEvent(enterFrame){\n   beida();\n}')
        timeline = json.loads((ROOT / 'godot/generated/fighters/yihu/timeline.json').read_text())
        frames = {f['frame']: f for f in timeline['frames']}
        for frame in (738, 739, 740):
            self.assertFalse(any(p.get('name') == 'bdmn' for p in frames[frame]['display_list']))
        receiver = next(p for p in frames[741]['display_list'] if p.get('name') == 'bdmn')
        self.assertEqual(receiver['placed_frame'], 741)

    def test_kon_retained_hitbox_and_independent_drains(self):
        model = build_model(ROOT / 'scripts/fighter/fz/kon.json',
                            ROOT / 'game/fighter/fz/kon.swf', '魂')
        self.assertEqual(model['end_frame'], 102)
        self.assertEqual(model['hide_frames'], [])
        self.assertEqual(model['hide_frame_events'], [])
        self.assertEqual(model['nested_stops'], [])
        self.assertEqual(model['clip_load_events'], [])
        self.assertEqual([(x['frame'], x['delta']) for x in model['drain_events']],
                         [(frame, -20.0) for frame in (72, 75, 78, 81, 85, 89)])
        timeline = json.loads((ROOT / 'godot/generated/helpers/kon/timeline.json').read_text())
        placements = [(f['frame'], p['placed_frame']) for f in timeline['frames']
                      for p in f['display_list'] if p.get('name') == 'atm1']
        self.assertEqual(placements, [(frame, 37) for frame in range(37, 65)])

    def test_hurt_timer_starts_with_the_placed_callback(self):
        for fighter, first_callback in [('minren', 1017), ('yihu', 741)]:
            model = json.loads((ROOT / f'godot/generated/fighters/{fighter}/combat.json').read_text())
            event = model['hurt']
            self.assertEqual(event['callback_start_frame'], first_callback)
            bundle = json.loads((ROOT / f'scripts/fighter/{fighter}.json').read_text())
            source = next(x['source'] for x in bundle['scripts'] if x['path'] == event['callback_source_path'])
            self.assertIn('_parent.beidax();', source)
            self.assertIn(f'/frame_{first_callback - 1}/PlaceObject', event['callback_source_path'])

    def test_original_comparator_rejects_changed_settlement(self):
        capture = ROOT / 'evidence/combat/helper-woailuo-r01'
        self.assertEqual(compare(capture / 'events.jsonl', capture / 'native.json')['status'], 'matched')
        rows = json.loads((capture / 'native.json').read_text())
        next(row for row in rows if row['hp'] < 1000)['hp'] += 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'changed.json'
            path.write_text(json.dumps(rows))
            result = compare(capture / 'events.jsonl', path)
        self.assertEqual(result['status'], 'first_difference')
        self.assertEqual(result['differences'][0]['field'], 'hp')
