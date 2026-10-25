import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from tools.probes.analyze_animated_rect_component import analyze
from tools.probes.extract_animated_rect_component import extract

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r142'


class AnimatedRectComponentTests(unittest.TestCase):
    def test_remaining_source_errors_and_coverage_guard_are_retained(self):
        r=analyze(EVIDENCE/'fixture.json',ROOT/'evidence/importer-loud-fail/r141/native')
        self.assertEqual(r,json.loads((EVIDENCE/'summary.json').read_text()))
        blocked=[v for v in r['rows'] if v.get('status')=='blocked']
        self.assertEqual([(v['tick'],v['native_frame'],v['shape_id']) for v in blocked],[(4,5,10)])
        self.assertEqual(len(blocked[0]['diagnosis']['nontransparent_fringe']),8)
        self.assertEqual([v['cache']['exact'] for v in r['rows'] if 'cache' in v],[239338,239316,239338])
        self.assertFalse(r['source_cpu_exact'])
        self.assertFalse(r['production_admitted'])

    def test_unknown_action_and_named_placement_still_reject(self):
        f=json.loads((EVIDENCE/'fixture.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            xml=Path(folder)/'source.xml'
            for kind in ('action','named'):
                root=ET.Element('swf');tags=ET.SubElement(root,'tags');wrapper=ET.fromstring(f['wrapper_xml']);tags.append(wrapper)
                for leaf in f['leaves'].values():tags.append(ET.fromstring(leaf['shape_xml']))
                if kind=='action':ET.SubElement(wrapper.find('subTags'),'item',{'type':'DoActionTag'})
                else:
                    placement=wrapper.find('./subTags/item[@type="PlaceObject2Tag"]')
                    placement.set('placeFlagHasName','true');placement.set('name','unknown_instance')
                xml.write_text(ET.tostring(root,encoding='unicode'))
                with self.assertRaisesRegex(ValueError,'Uncompiled animated wrapper tag|Unconsumed placement fields'):
                    extract(xml,ROOT/'evidence/importer-loud-fail/r21/components/lanran/cases.json',f['case']['id'])

    def test_source_and_evidence_pins(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():
                self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
