"""Source shape 107 excludes the ice even though its AABB includes it."""
import json
import copy
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from bitmap_shape_polygon import bitmap_shape_polygon
from bitmap_shape_polygon import bitmap_shape_fill_polygons
from extract_timeline_geometry import referenced_definitions


class BitmapShapePolygonTests(unittest.TestCase):
    def setUp(self):
        self.shape = ET.parse(ROOT / 'evidence/visual-audio/bitmap-shape-clip/shape107.xml').getroot()

    def test_source_curve_is_retained_in_both_timeline_artifacts(self):
        polygon = bitmap_shape_polygon(self.shape)
        self.assertEqual(polygon[0], [103.65, 80.35])
        self.assertIn([17.4, 58.5], polygon)
        self.assertIn([109.45, 58.5], polygon)
        for path in ['data/slices/rifagu-base.timeline.json', 'godot/generated/fighters/rifagu/timeline.json']:
            definitions = json.loads((ROOT / path).read_text())['definitions']
            shape = next(d for d in definitions if d['character_id'] == 107)
            self.assertEqual(shape['bitmap_clip_polygon'], polygon)

    def test_multiple_contours_require_fill_rule_aware_compilation(self):
        records = self.shape.find('./shapes/shapeRecords')
        records.append(ET.Element('item', type='StyleChangeRecord', stateMoveTo='true'))
        self.assertIsNone(bitmap_shape_polygon(self.shape))

    def test_rukia_composite_u_shape_compiles_each_source_fill_boundary(self):
        source = ET.parse(ROOT / 'evidence/characters/rukia/u-duplicate-mask-r01/shape230.xml').getroot()
        shape = source.find('item')
        polygons = bitmap_shape_fill_polygons(shape)
        self.assertEqual(len(polygons), 3)
        self.assertEqual(polygons[0], [[[0.0, 0.0], [101.55, 0.0], [101.55, 47.0], [0.0, 47.0]]])
        self.assertEqual(polygons[1], [[[136.5, 46.75], [93.0, 46.75], [93.0, -0.25], [136.5, -0.25]]])
        self.assertEqual(polygons[2], [[[136.5, -0.25], [213.5, -0.25], [213.5, 46.75], [136.5, 46.75]]])
        for path in ['data/slices/rukia-base.timeline.json', 'godot/generated/fighters/rukia/timeline.json']:
            definitions = json.loads((ROOT / path).read_text())['definitions']
            compiled_shape = next(definition for definition in definitions if definition['character_id'] == 230)
            self.assertEqual(compiled_shape['bitmap_clip_polygons'], polygons)

    def test_ambiguous_new_styles_and_open_fill_contours_fall_back(self):
        source = ET.parse(ROOT / 'evidence/characters/rukia/u-duplicate-mask-r01/shape230.xml').getroot()
        new_styles_shape = copy.deepcopy(source.find('item'))
        new_styles = next(
            record for record in new_styles_shape.findall('./shapes/shapeRecords/item')
            if record.get('stateNewStyles') == 'true'
        )
        new_styles.set('stateFillStyle0', 'false')
        self.assertIsNone(bitmap_shape_fill_polygons(new_styles_shape))

        open_shape = copy.deepcopy(source.find('item'))
        records = open_shape.findall('./shapes/shapeRecords/item')
        open_shape.find('./shapes/shapeRecords').remove(records[-2])
        self.assertIsNone(bitmap_shape_fill_polygons(open_shape))

    def test_gin_placeholder_keeps_blade_masks_aligned(self):
        for shape_id, count in [(180, 3), (182, 5), (224, 3), (226, 6)]:
            shape = ET.parse(
                ROOT / f'evidence/visual-audio/bitmap-placeholder-mask/yin-shape{shape_id}.xml'
            ).getroot()
            polygons = bitmap_shape_fill_polygons(shape)
            self.assertEqual(len(polygons), count)
            self.assertEqual(polygons[0], [])
            self.assertTrue(all(polygons[1:]))
            for path in ['data/slices/yin-base.timeline.json', 'godot/generated/fighters/yin/timeline.json']:
                definitions = json.loads((ROOT / path).read_text())['definitions']
                compiled = next(d for d in definitions if d['character_id'] == shape_id)
                self.assertEqual(compiled['bitmap_clip_polygons'], polygons)

    def test_unused_real_bitmap_fill_also_paints_nothing(self):
        shape = ET.parse(
            ROOT / 'evidence/visual-audio/bitmap-placeholder-mask/yin-shape180.xml'
        ).getroot()
        shape.find('./shapes/fillStyles/fillStyles/item').set('bitmapId', '123')
        polygons = bitmap_shape_fill_polygons(shape)
        self.assertEqual(polygons[0], [])
        self.assertEqual(len(polygons), 3)

    def test_single_unused_fill_is_emitted_as_an_explicit_empty_mask(self):
        # A declared fill alone does not paint; source edges must use it.
        root = ET.fromstring('''<swf><tags>
          <item type="DefineShapeTag" shapeId="1"><shapes>
            <fillStyles><fillStyles><item bitmapId="123" fillStyleType="65"/></fillStyles></fillStyles>
            <shapeRecords><item type="EndShapeRecord"/></shapeRecords>
          </shapes></item>
        </tags></swf>''')
        definitions = referenced_definitions(root, [{'display_list': [{'character_id': 1}]}])
        self.assertEqual(definitions[0]['bitmap_clip_polygons'], [[]])

    def test_empty_fill_does_not_hide_open_nonempty_contours(self):
        shape = ET.parse(
            ROOT / 'evidence/visual-audio/bitmap-placeholder-mask/yin-shape180.xml'
        ).getroot()
        records = shape.find('./shapes/shapeRecords')
        edge = next(r for r in records if r.get('type') == 'StraightEdgeRecord')
        records.remove(edge)
        self.assertIsNone(bitmap_shape_fill_polygons(shape))


if __name__ == '__main__':
    unittest.main()
