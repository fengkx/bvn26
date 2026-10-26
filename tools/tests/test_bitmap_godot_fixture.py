import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.build_bitmap_godot_fixture import build, rgba_capture
from tools.probes.run_bitmap_godot_fixture import validate_report

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r32'


class BitmapGodotFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = build()
        cls.report = json.loads((EVIDENCE/'gpu.json').read_text())
        cls.provenance = json.loads((EVIDENCE/'provenance.json').read_text())

    def test_fixture_is_native_backed_and_matches_gpu_evidence(self):
        self.assertEqual(self.fixture['samples'], 71824)
        data = (json.dumps(self.fixture, separators=(',', ':'))+'\n').encode()
        digest = hashlib.sha256(data).hexdigest()
        self.assertEqual(digest, self.provenance['fixture_sha256'])
        validate_report(self.report, self.fixture, digest)
        self.assertEqual(self.report['scores']['rgba-varying'], {'samples': 4368, 'exact': 4368})
        self.assertEqual(self.report['scores']['rgba-constant'], {'samples': 4368, 'exact': 4368})
        for path, expected in self.provenance['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), expected, path)
        self.assertEqual(hashlib.sha256((EVIDENCE/'gpu.png').read_bytes()).hexdigest(),
                         self.provenance['readback_sha256'])

    def test_inexact_missing_and_wrong_input_reports_are_rejected(self):
        for field, value in [('exact', 71823), ('samples', 0), ('failures', [{}]),
                             ('fixture_sha256', 'wrong'), ('production_admitted', True), ('scores', {})]:
            report = copy.deepcopy(self.report)
            report[field] = value
            with self.assertRaises(ValueError):
                validate_report(report, self.fixture, self.provenance['fixture_sha256'])

    def test_rgba_capture_is_complete_and_source_pinned(self):
        text = (EVIDENCE/'rgba/native.log').read_text()
        rows = rgba_capture(text)
        self.assertEqual(len(rows), 128)
        self.assertEqual(sum(len(pixels) for _, pixels in rows), 8736)
        build_data = json.loads((EVIDENCE/'rgba/build.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT/build_data['source']).read_bytes()).hexdigest(),
                         build_data['source_sha256'])
        for bad in (text+text, text.replace('|done|ok', '|done|bad'),
                    text.replace('-r32-', '-r31-', 1), text.replace('|rgba|0,0,3,3,1,', '|rgba|0,0,3,3,2,', 1)):
            with self.assertRaises(ValueError):
                rgba_capture(bad)

    def test_production_component_mismatches_still_block_admission(self):
        components = json.loads((EVIDENCE/'component-comparison.json').read_text())
        self.assertEqual((components['images_matched'], components['images']), (9, 54))
        self.assertEqual((components['clock_samples'], components['clock_differences']), (4242, 0))
        self.assertFalse(components['passed'])
        self.assertFalse(self.report['production_admitted'])
