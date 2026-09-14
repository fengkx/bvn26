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


if __name__ == '__main__':
    unittest.main()
