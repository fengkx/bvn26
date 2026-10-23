"""Unsupported placement revisions must not disappear from display lists."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'importer'))
from audit_importer import audit_xml
from extract_timeline_geometry import build_frames, extract_wrapper_placement, placement_delta


class PlacementTagGuardsTests(unittest.TestCase):
    def test_unsupported_placement_revisions_fail_instead_of_skipping(self):
        for kind in ('PlaceObjectTag', 'PlaceObject4Tag', 'PlaceObjectFutureTag'):
            tag = ET.Element('item', type=kind, depth='4', characterId='7')
            with self.subTest(kind=kind), self.assertRaisesRegex(
                    ValueError, 'fixture.swf/DefineSprite_9/frame_1/depth_4: unsupported placement tag ' + kind):
                build_frames([tag, ET.Element('item', type='ShowFrameTag')], 'fixture.swf/DefineSprite_9')
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'unsupported placement tag ' + kind):
                placement_delta(tag, 'fixture.swf/frame_1')
            root = ET.fromstring('<swf><tags/></swf>')
            root.find('tags').append(tag)
            with self.subTest(kind=kind), self.assertRaisesRegex(
                    ValueError, 'fixture.swf/root/frame_1/depth_4: unsupported placement tag ' + kind):
                extract_wrapper_placement(root, 7, 'fixture.swf')
            failures = audit_xml(root, 'fixture.swf')['failures']
            self.assertEqual(len(failures), 1)
            self.assertEqual(failures[0]['construct'], kind)
            self.assertEqual(failures[0]['depth'], 4)

    def test_sprite_wrapper_ratio_is_preserved_without_morph_interpolation(self):
        root = ET.fromstring('''<swf><tags>
            <item type="DefineSpriteTag" spriteId="7"><subTags/></item>
            <item type="PlaceObject3Tag" depth="1" characterId="7" ratio="2"/>
            </tags></swf>''')
        self.assertEqual(extract_wrapper_placement(root, 7, 'fixture.swf')['ratio'], 2)
        self.assertEqual(audit_xml(root, 'fixture.swf')['failures'], [])
        root.find('./tags/item').attrib = {'type': 'DefineMorphShapeTag', 'shapeId': '7'}
        self.assertEqual(audit_xml(root, 'fixture.swf')['failures'][0]['construct'], 'morph ratio')

    def test_wrapper_cannot_drop_supported_child_filter(self):
        root = ET.fromstring('''<swf><tags>
            <item type="PlaceObject3Tag" depth="1" characterId="345">
            <surfaceFilterList><item type="BLURFILTER" blurX="0" blurY="0" passes="1"/></surfaceFilterList>
            </item></tags></swf>''')
        self.assertEqual(audit_xml(root, 'fixture.swf')['wrapper_obligations'][0]['character_id'], 345)
        self.assertEqual(extract_wrapper_placement(root, 345, 'fixture.swf')['filters'],
                         [{'type': 'BLURFILTER', 'blurX': 0.0, 'blurY': 0.0, 'passes': 1}])

    def test_cached_wrapper_cannot_bypass_source_filter(self):
        import json
        from unittest.mock import patch
        from placement_build_guard import validate_build_placements
        fields = {'filters': [{'type': 'BLURFILTER', 'blurX': 0, 'blurY': 0, 'passes': 1}]}
        catalog = {'abc': {'swf': 'fixture.swf', 'records': [], 'obligations': [
            {'sprite': 0, 'frame': 1, 'depth': 1, 'fields': fields}]}}
        catalog['abc']['wrapper_obligations'] = [{'character_id': 345, 'frame': 1, 'depth': 1, 'fields': fields}]
        timeline = {'source_swf': {'sha256': 'abc'}, 'sprite_id': 345, 'frames': [],
                    'definitions': [], 'wrapper': {'root_frame': 1, 'depth': 1}}
        with patch('placement_build_guard.Path.read_text', return_value=json.dumps(catalog)):
            with self.assertRaisesRegex(ValueError, 'dropped/changed wrapper filters: fixture.swf/root/frame_1/depth_1'):
                validate_build_placements(timeline, 'cache.json')
            del timeline['wrapper']
            with self.assertRaisesRegex(ValueError, 'dropped/changed wrapper filters'):
                validate_build_placements(timeline, 'cache.json')

    def test_wrapper_field_error_keeps_root_location(self):
        root = ET.fromstring('''<swf><tags><item type="ShowFrameTag"/>
            <item type="PlaceObject3Tag" depth="5" characterId="7" blendMode="13"/>
            </tags></swf>''')
        with self.assertRaisesRegex(ValueError, 'fixture.swf/root/frame_2/depth_5'):
            extract_wrapper_placement(root, 7, 'fixture.swf')


if __name__ == '__main__':
    unittest.main()
