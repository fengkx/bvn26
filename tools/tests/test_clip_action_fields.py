"""Reject metadata that used to disappear before clip action ownership checks."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'importer'))
from extract_timeline_geometry import placement_delta
from audit_importer import audit_xml

SOURCE = 'fixture.swf/DefineSprite_7/frame_3/depth_2'


def placement():
    return ET.fromstring('''<item type="PlaceObject2Tag" depth="2" characterId="8">
      <clipActions type="CLIPACTIONS" reserved="0">
        <allEventFlags clipEventLoad="true"/>
        <clipActionRecords><item actionBytes="00" keyCode="0">
          <eventFlags clipEventLoad="true"/>
        </item></clipActionRecords>
      </clipActions></item>''')


class ClipActionFieldsTests(unittest.TestCase):
    def test_guard_imports_work_in_package_mode(self):
        import subprocess
        result = subprocess.run([sys.executable, '-c',
            'from tools.importer.import_guards import finite_numbers; '
            'from tools.importer.placement_build_guard import validate_build_placements'],
            cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_valid_event_metadata_is_preserved(self):
        result = placement_delta(placement(), SOURCE)
        self.assertEqual(result['clip_actions'][0]['events'], ['Load'])
        self.assertEqual(len(result['clip_actions'][0]['action_bytes_sha256']), 64)

    def test_dropped_fields_and_malformed_records_fail_at_source(self):
        base = placement()
        edits = [
            ('.//clipActions', 'type', 'OTHER'),
            ('.//clipActions', 'reserved', '1'),
            ('.//clipActions', 'unknown', '1'),
            ('.//allEventFlags', 'clipEventLoad', 'false'),
            ('.//eventFlags', 'clipEventLoad', 'maybe'),
            ('.//eventFlags', 'clipEventFuture', 'true'),
            ('.//eventFlags', 'reserved2', '1'),
            ('.//clipActionRecords/item', 'keyCode', '65'),
            ('.//clipActionRecords/item', 'unknown', '1'),
            ('.//clipActionRecords/item', 'actionBytes', ''),
            ('.//clipActionRecords/item', 'actionBytes', '0'),
            ('.//clipActionRecords/item', 'actionBytes', 'zz'),
        ]
        for path, field, value in edits:
            tag = deepcopy(base)
            tag.find(path).set(field, value)
            with self.subTest(path=path, field=field, value=value), self.assertRaisesRegex(ValueError, SOURCE):
                placement_delta(tag, SOURCE)
        for path in ('.//allEventFlags', './/clipActionRecords/item/eventFlags'):
            tag = deepcopy(base)
            child = tag.find(path)
            parent = next(e for e in tag.iter() if child in list(e))
            parent.remove(child)
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, SOURCE):
                placement_delta(tag, SOURCE)

    def test_keypress_zero_keycode_is_not_silently_relabelled(self):
        tag = placement()
        for flags in (tag.find('.//eventFlags'), tag.find('.//allEventFlags')):
            flags.attrib.clear()
            flags.set('clipEventKeyPress', 'true')
        with self.assertRaisesRegex(ValueError, 'unsupported clip action keyCode/KeyPress'):
            placement_delta(tag, SOURCE)

    def test_clip_obligation_covers_moves_and_stops_at_replacement(self):
        root = ET.fromstring('<swf><tags/></swf>')
        tags = root.find('tags')
        tags.append(placement())
        tags.append(ET.Element('item', type='ShowFrameTag'))
        tags.append(ET.Element('item', type='PlaceObject2Tag', depth='2', placeFlagMove='true'))
        tags.append(ET.Element('item', type='ShowFrameTag'))
        tags.append(ET.Element('item', type='PlaceObject2Tag', depth='2', characterId='9'))
        tags.append(ET.Element('item', type='ShowFrameTag'))
        rows = audit_xml(root, 'fixture.swf')['clip_action_obligations']
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]['first_frame'], rows[0]['last_frame']), (1, 2))
        self.assertEqual(rows[0]['clip_actions'][0]['events'], ['Load'])

    def test_cached_clip_action_mutations_fail_on_inherited_frame(self):
        import json
        from unittest.mock import patch
        from placement_build_guard import validate_build_placements
        actions = placement_delta(placement(), SOURCE)['clip_actions']
        catalog = {'abc': {'swf': 'fixture.swf', 'records': [], 'obligations': [],
                          'clip_action_obligations': [{'sprite': 7, 'first_frame': 1,
                              'last_frame': 2, 'depth': 2, 'clip_actions': actions}]}}
        timeline = {'source_swf': {'sha256': 'abc'}, 'sprite_id': 7,
                    'frames': [{'frame': n, 'display_list': [{'depth': 2, 'clip_actions': deepcopy(actions)}]}
                               for n in (1, 2)], 'definitions': []}
        with patch('placement_build_guard.Path.read_text', return_value=json.dumps(catalog)):
            validate_build_placements(timeline, 'cache.json')
            for field, value in (('events', ['EnterFrame']), ('action_bytes_sha256', 'changed')):
                changed = deepcopy(timeline)
                changed['frames'][1]['display_list'][0]['clip_actions'][0][field] = value
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'clip_actions.*fixture.swf sprite 7 frame 2 depth 2'):
                    validate_build_placements(changed, 'cache.json')
            changed = deepcopy(timeline)
            del changed['frames'][1]['display_list'][0]['clip_actions']
            with self.assertRaisesRegex(ValueError, 'clip_actions.*frame 2'):
                validate_build_placements(changed, 'cache.json')
            nested = {'source_swf': {'sha256': 'abc'}, 'sprite_id': 9, 'frames': [],
                      'definitions': [{'type': 'DefineSpriteTag', 'character_id': 7,
                          'display_list_frames': [f['display_list'] for f in changed['frames']]}]}
            with self.assertRaisesRegex(ValueError, 'clip_actions.*frame 2'):
                validate_build_placements(nested, 'cache.json')

    def test_cache_guard_does_not_accept_numeric_boolean(self):
        import json
        from unittest.mock import patch
        from placement_build_guard import validate_build_placements
        catalog = {'abc': {'swf': 'fixture.swf', 'records': [], 'obligations': [
            {'sprite': 7, 'frame': 3, 'depth': 2, 'fields': {'cache_as_bitmap': True}}]}}
        timeline = {'source_swf': {'sha256': 'abc'}, 'sprite_id': 7,
                    'frames': [{'frame': 3, 'display_list': [{'depth': 2, 'cache_as_bitmap': 1}]}],
                    'definitions': []}
        with patch('placement_build_guard.Path.read_text', return_value=json.dumps(catalog)):
            with self.assertRaisesRegex(ValueError, 'changed cache_as_bitmap.*fixture.swf sprite 7 frame 3 depth 2'):
                validate_build_placements(timeline, 'cache.json')

    def test_failure_inventory_includes_exact_placement(self):
        root = ET.fromstring('<swf><tags><item type="PlaceObject3Tag" depth="8" blendMode="13"/></tags></swf>')
        failure = audit_xml(root, 'fixture.swf')['failures'][0]
        self.assertEqual(failure['source'], 'fixture.swf/root/frame_1')
        self.assertEqual(failure['depth'], 8)
        self.assertIn('blendMode="13"', failure['placement_xml'])


if __name__ == '__main__':
    unittest.main()
