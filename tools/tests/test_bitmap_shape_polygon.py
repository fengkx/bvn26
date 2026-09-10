"""Source shape 107 excludes the ice even though its AABB includes it."""
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from bitmap_shape_polygon import bitmap_shape_polygon


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


if __name__ == '__main__':
    unittest.main()
