import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.run_native_nested_filters import fixture
from tools.probes.run_nested_filters import compare, decode

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r59/render'
NATIVE = ROOT / 'evidence/importer-loud-fail/r38/native'


class NativeNestedFilterTests(unittest.TestCase):
    def test_actual_filter_buffers_match_pinned_native(self):
        report = compare(decode(NATIVE), EVIDENCE)
        self.assertTrue(report['passed'])
        self.assertEqual((report['exact'], report['pixels']), (72576, 72576))
        self.assertFalse(report['production_admitted'])

    def test_cpu_admission_and_reciprocal_upload_fixture_are_preserved(self):
        actual = json.loads((EVIDENCE / 'fixture.json').read_text())
        self.assertEqual(actual, fixture())
        self.assertTrue(actual['cpu_arithmetic_passed'])
        self.assertFalse(actual['production_admitted'])
        self.assertEqual(len(actual['native_reciprocals']), 256)
        log = (EVIDENCE / 'godot.log').read_text()
        self.assertIn('NATIVE_CXFORM_BINDINGS_OK sprites=336 groups=96 production_admitted=false', log)
        self.assertNotIn('ERROR', log)

    def test_sources_references_and_readbacks_are_pinned(self):
        provenance = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, directory in [('source_sha256', ROOT), ('native_sha256', NATIVE),
                               ('readback_sha256', EVIDENCE)]:
            for name, expected in provenance[key].items():
                self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), expected, name)
