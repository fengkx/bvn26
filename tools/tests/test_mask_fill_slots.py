"""Unused Flash fill slots do not turn one rectangular mask into many masks."""
import copy
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
from extract_timeline_geometry import referenced_definitions


class MaskFillSlotTests(unittest.TestCase):
    def shape(self):
        # JPEXS export of locked Byakuya.swf DefineShape882; style 1 is unused.
        return ET.parse(Path(__file__).parent / 'fixtures/byakuya_mask882.xml').getroot()

    def extract(self, shape):
        root = ET.Element('swf')
        tags = ET.SubElement(root, 'tags')
        tags.append(shape)
        ET.SubElement(tags, 'item', type='PlaceObject2Tag', characterId='882',
                      placeFlagHasClipDepth='true', clipDepth='29')
        return referenced_definitions(root, [{'frame': 1, 'display_list': [{'character_id': 882}]}])[0]

    def test_source_unused_fill_slot_keeps_exact_rectangle(self):
        self.assertEqual(self.extract(self.shape())['mask_polygon'],
                         [[-31.75, -42.15], [28.55, -42.15], [28.55, 30.15], [-31.75, 30.15]])

    def test_second_used_fill_remains_hard_error(self):
        shape = self.shape()
        records = shape.find('./shapes/shapeRecords')
        additional = [copy.deepcopy(record) for record in list(records)[:-1]]
        additional[0].set('fillStyle0', '1')
        records.remove(records[-1])
        records.extend(additional)
        ET.SubElement(records, 'item', type='EndShapeRecord', endOfShape='0')
        with self.assertRaisesRegex(ValueError, 'Unsupported clipDepth mask geometry: 882'):
            self.extract(shape)
