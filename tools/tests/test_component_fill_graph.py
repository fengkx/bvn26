import hashlib
import json
from pathlib import Path
import struct
import unittest
import xml.etree.ElementTree as ET
from tools.probes.build_bound_bitmap_component import source_tags,bitmap_shape_fill_polygons

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r132'


class ComponentFillGraphTests(unittest.TestCase):
    def test_authored_slots_and_active_rotated_contour(self):
        result=json.loads((EVIDENCE/'summary.json').read_text())
        shape=ET.parse(EVIDENCE/'shape.xml').getroot()
        self.assertEqual(bitmap_shape_fill_polygons(shape),[v['contours'] for v in result['fills']])
        self.assertEqual([v['directed_edge_count'] for v in result['fills']],[0,4])
        self.assertEqual([v['style']['bitmapId'] for v in result['fills']],['65535','148'])
        active=result['fills'][1]
        self.assertEqual(active['contours'],[active['transformed_bitmap_corners']])
        self.assertEqual(active['bitmap']['width'],34)
        self.assertTrue(result['requires_quarter_turn_sampler'])
        self.assertFalse(result['production_admitted'])
        source=ROOT/result['case']['source']['path']
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),result['case']['source']['sha256'])
        tags={str(struct.unpack_from('<H',p)[0]):r for code,p,r in source_tags(source) if code in (2,36,39)}
        for cid,digest in result['raw_tag_sha256'].items():
            self.assertEqual(hashlib.sha256(tags[cid]).hexdigest(),digest)

    def test_inspector_and_evidence_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
