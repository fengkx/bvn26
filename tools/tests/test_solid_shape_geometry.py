"""Retain the source curved upper-special paint rather than its bounds."""
import copy
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from solid_shape_geometry import solid_fill_polygons, solid_closed_strokes
from extract_timeline_geometry import referenced_definitions


class SolidShapeGeometryTests(unittest.TestCase):
    def setUp(self):
        self.shape = ET.parse(ROOT / 'evidence/characters/selected-forms/live-2026-11-17/red-block/shape948.xml').getroot()

    def test_source_curves_keep_their_endpoints_and_exclude_bounds_corners(self):
        contour = solid_fill_polygons(self.shape)[0][0]
        self.assertIn([100, -27.1], contour)
        self.assertIn([128, 40.45], contour)
        self.assertNotIn([-63.5, -55.55], contour)
        self.assertGreater(len(contour), 8)

    def test_closed_source_stroke_keeps_width_color_and_boundary(self):
        strokes = solid_closed_strokes(self.shape)
        self.assertEqual(strokes[0]['width'], 1)
        self.assertEqual(strokes[0]['color'], {'red': 255, 'green': 0, 'blue': 0, 'alpha': 255})
        self.assertEqual(strokes[0]['paths'], solid_fill_polygons(self.shape)[0])

    def test_timeline_extractor_emits_the_source_paint(self):
        root = ET.Element('swf')
        tags = ET.SubElement(root, 'tags')
        tags.append(copy.deepcopy(self.shape))
        definitions = referenced_definitions(root, [{'display_list': [{'character_id': 948}]}])
        self.assertEqual(definitions[0]['solid_fill_polygons'], solid_fill_polygons(self.shape))
        self.assertEqual(definitions[0]['solid_closed_strokes'], solid_closed_strokes(self.shape))

    def test_unused_fill_paints_nothing(self):
        shape = copy.deepcopy(self.shape)
        for record in shape.findall('./shapes/shapeRecords/item'):
            if record.get('type') == 'StyleChangeRecord':
                record.set('fillStyle1', '0')
        self.assertEqual(solid_fill_polygons(shape), [[]])

    def test_non_scaling_stroke_is_not_silently_approximated(self):
        self.shape.find('./shapes/lineStyles/lineStyles2/item').set('noHScaleFlag', 'true')
        self.assertIsNone(solid_closed_strokes(self.shape))


if __name__ == '__main__':
    unittest.main()
