"""Native shadow phase evidence and strict placement admission regressions."""
import json
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/probes'))
sys.path.insert(0, str(ROOT/'tools/importer'))
from analyze_shadow_phase import decode, impulse
from visual_filters import compile_filters


class DropShadowTests(unittest.TestCase):
    def source_filter(self):
        record = json.loads((ROOT/'evidence/importer-loud-fail/r19/remaining-placements.json').read_text())[0]
        return ET.fromstring(record['placement_xml']).find('surfaceFilterList')

    def test_native_phase_and_sweep(self):
        for name, count in [('shadow-phase', 48), ('shadow-phase-sweep', 520), ('shadow-phase-ties', 48)]:
            rows = json.loads((ROOT/f'tools/probes/flash_filters/{name}-native.json').read_text())
            self.assertEqual(len(rows), count)
            for index, row in enumerate(rows):
                with self.subTest(fixture=name, case=index):
                    self.assertEqual(impulse(row), row['pixels'])

    def test_incomplete_capture_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            decode([], 48)

    def test_authored_shadow_keeps_offset_and_filter_fields(self):
        row, = compile_filters(self.source_filter(), 'main.swf/DefineSprite_1504/frame_1/depth_6')
        self.assertEqual(row, {'type': 'DROPSHADOWFILTER', 'blurX': 3, 'blurY': 3, 'passes': 1,
                              'strength': 3, 'angle': 0.7853851318359375, 'distance': 1,
                              'color': [0, 0, 0, 1]})

    def test_unimplemented_variants_and_malformed_fields_fail_at_source(self):
        changes = [('innerShadow', 'true'), ('knockout', 'true'), ('compositeSource', 'false'),
                   ('angle', 'NaN'), ('distance', 'Infinity'), ('angle', None), ('distance', None),
                   ('id', '2'), ('unhandled', 'true')]
        for field, value in changes:
            filters = self.source_filter()
            if value is None:
                del filters[0].attrib[field]
            else:
                filters[0].set(field, value)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'fixture.swf/frame_1/depth_6:'):
                compile_filters(filters, 'fixture.swf/frame_1/depth_6')


if __name__ == '__main__':
    unittest.main()
