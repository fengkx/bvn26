import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from tools.probes.extract_rect_control_graph import extract
from tools.probes.analyze_rect_control_graph import analyze
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'evidence/importer-loud-fail/r156'

class RectControlGraphTests(unittest.TestCase):
    def fixture(self,name):return json.loads(gzip.decompress((EVIDENCE/(name+'-fixture.json.gz')).read_bytes()))

    def test_native_clocks_and_explicit_empty_frames(self):
        for name in ('main','yijiao'):
            f=self.fixture(name);r=analyze(f)
            self.assertEqual(r,json.loads((EVIDENCE/(name+'-summary.json')).read_text()))
            self.assertTrue(r['diagnostic_clock_exact'])
            self.assertFalse(r['production_admitted'])
            self.assertFalse(r['full_as_ownership_proved'])
        self.assertEqual(analyze(self.fixture('main'))['empty_frames'],[17])
        self.assertEqual(analyze(self.fixture('yijiao'))['empty_frames'],list(range(13,51)))

    def test_unknown_actions_and_unowned_removals_reject(self):
        f=self.fixture('main');root=ET.Element('swf');tags=ET.SubElement(root,'tags');wrapper=ET.fromstring(f['wrapper_xml']);tags.append(wrapper)
        for leaf in f['leaves'].values():tags.append(ET.fromstring(leaf['shape_xml']))
        cases=ROOT/'evidence/importer-loud-fail/r32/components/main/cases.json'
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'source.xml';ET.ElementTree(root).write(path)
            rebuilt=extract(path,cases,f['case']['id'])
            for key in ('frames','actions','raw_tag_sha256'):self.assertEqual(rebuilt[key],f[key])
            action=wrapper.find('./subTags/item[@type="DoActionTag"]');action.set('actionBytes','0600');ET.ElementTree(root).write(path)
            with self.assertRaisesRegex(ValueError,'DefineSprite_297/frame_17: unsupported action opcode0x06'):extract(path,cases,f['case']['id'])
            action.set('actionBytes','0700');wrapper.find('./subTags/item[@type="RemoveObject2Tag"]').set('depth','2');ET.ElementTree(root).write(path)
            with self.assertRaisesRegex(ValueError,'frame_17: unowned removal'):extract(path,cases,f['case']['id'])

    def test_provenance(self):
        p=json.loads((EVIDENCE/'provenance.json').read_text())
        for key,root in [('source_sha256',ROOT),('evidence_sha256',EVIDENCE)]:
            for name,digest in p[key].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
