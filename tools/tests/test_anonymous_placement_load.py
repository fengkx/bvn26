import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from build_combat_model import build_model
from materialize_timeline_assets import materialize
from source_instance_key import instance_key


class AnonymousPlacementLoadTests(unittest.TestCase):
    def test_load_position_is_bound_to_placement_without_source_name(self):
        directory = ROOT / 'godot/generated/fighters/itachi'
        timeline = json.loads((directory / 'timeline.json').read_text())
        placement = next(p for f in timeline['frames'] if f['frame'] == 305
                         for p in f['display_list'] if p['depth'] == 31)
        placement.pop('name')
        handle = instance_key(placement)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'timeline.json'
            path.write_text(json.dumps(timeline))
            model = build_model(directory / 'fighter.json', path, ROOT / 'scripts/fighter/itachi.json')
        event = next(e for e in model['clip_placements'] if e['frame'] == 305)
        self.assertEqual(event['instance_name'], handle)
        self.assertEqual(event['op'], 'place_at_opponent')
        self.assertTrue(event['place_x'])
        self.assertIn('PlaceObject2_61_31/', event['source_path'])

    def test_materialization_exposes_internal_handle_only_for_compiled_receiver(self):
        placement = {'depth': 34, 'character_id': 654, 'placed_frame': 418}
        timeline = {'frames': [{'frame': 418, 'display_list': [placement,
                    {'depth': 35, 'character_id': 655, 'placed_frame': 418}]}], 'definitions': []}
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'timeline.json').write_text(json.dumps(timeline))
            (work / 'combat.json').write_text(json.dumps({'clip_placements': [
                {'instance_name': instance_key(placement), 'op': 'place_at_opponent'}]}))
            materialize(work, work / 'timeline.json', work / 'out', combat_model_path=work / 'combat.json')
            result = json.loads((work / 'out/timeline.json').read_text())['frames'][0]['display_list']
        self.assertEqual(result[0]['name'], '@placement:34:654:418')
        self.assertTrue(result[0]['runtime_only_name'])
        self.assertNotIn('name', result[1])
        self.assertNotIn('name', placement)


if __name__ == '__main__':
    unittest.main()
