import copy
import hashlib
import json
from pathlib import Path
import unittest
import tempfile
import xml.etree.ElementTree as ET
from unittest.mock import patch
from tools.probes.extract_rect_component_leaf import extract
from tools.probes.analyze_rect_component_cache import analyze,load_fixture
from tools.probes.rect_mask_binding import canonical_rect_mask

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r129'


class RectComponentCacheTests(unittest.TestCase):
    def test_original_cyclic_mask_reproduces_native_boundaries(self):
        result=analyze(EVIDENCE/'fixture',ROOT/'evidence/importer-loud-fail/r128/native')
        self.assertEqual(result,json.loads((EVIDENCE/'summary.json').read_text()))
        self.assertEqual(result['authored_fill_masks'],[[[[80,0],[80,100],[0,100],[0,0]]]])
        for score in result['comparisons'].values():self.assertEqual(score['exact'],240000)
        self.assertEqual(sum(v['exact'] for v in result['pinned_comparisons']),480000)
        self.assertTrue(result['source_derived_cpu_component_exact'])
        self.assertFalse(result['production_admitted'])

    def test_only_cyclic_start_is_normalized_without_mutating_source(self):
        fixture=load_fixture(EVIDENCE/'fixture');before=copy.deepcopy(fixture)
        expected=[[[[0,0],[80,0],[80,100],[0,100]]]]
        self.assertEqual(canonical_rect_mask(fixture),expected)
        self.assertEqual(fixture,before)
        for start in range(4):
            points=expected[0][0];fixture['fill_masks']=[[points[start:]+points[:start]]]
            self.assertEqual(canonical_rect_mask(fixture),expected)
        for mask in ([[[[0,0],[80,100],[80,0],[0,100]]]],[[list(reversed(expected[0][0]))]],[[expected[0][0],expected[0][0]]],[[[[0,0],[79,0],[80,100],[0,100]]]]):
            fixture['fill_masks']=mask
            with self.assertRaises(ValueError):canonical_rect_mask(fixture)

    def test_extractor_rejects_uncompiled_actions_and_placement_fields(self):
        original=load_fixture(EVIDENCE/'fixture')
        for mode in ('action','named_placement','outer_color'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                folder=Path(temporary);case=copy.deepcopy(original['case'])
                wrapper=ET.fromstring(original['wrapper_xml'])
                if mode=='action':
                    ET.SubElement(wrapper.find('subTags'),'item',type='DoActionTag')
                elif mode=='named_placement':
                    placement=wrapper.find('./subTags/item[@type="PlaceObject2Tag"]')
                    placement.set('placeFlagHasName','true');placement.set('name','uncompiled')
                else:
                    case['placement']['color_transform']={'redMultTerm':128}
                cases=folder/'cases.json';cases.write_text(json.dumps([case]))
                ffdec=folder/'synthetic.jar';ffdec.write_bytes(b'test-only command stub')
                def exported(command,**kwargs):
                    root=ET.Element('swf');tags=ET.SubElement(root,'tags')
                    tags.append(wrapper);tags.append(ET.fromstring(original['shape_xml']))
                    Path(command[-1]).write_text(ET.tostring(root,encoding='unicode'))
                with patch('tools.probes.extract_rect_component_leaf.subprocess.run',side_effect=exported):
                    with self.assertRaises(ValueError):extract(cases,case['id'],folder/'output',ffdec)

    def test_sources_and_native_references_are_pinned(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
