import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_shadow_colored_paths import analyze, decode

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r82'


class ShadowColoredPathTests(unittest.TestCase):
    def test_common_source_composition_preserves_api_phase(self):
        report = analyze(EVIDENCE / 'native')
        self.assertEqual(report, json.loads((EVIDENCE / 'analysis.json').read_text()))
        self.assertTrue(report['passed'])
        self.assertFalse(report['production_admitted'])
        self.assertEqual(report['input_api_pairs_exact'], 73728)
        self.assertEqual(report['blur_alpha_exact'], 73728)
        self.assertEqual(report['output_api_pairs_exact'], 73162)
        for path in ('apply', 'display'):
            self.assertEqual(report['scores'][path], {'exact': 73728, 'samples': 73728, 'failures': []})
        for case in decode(EVIDENCE / 'native'):
            if case['filtered'] != case['display']:
                self.assertEqual(case['key'][7:9], [0, -0.501953125])

    def test_sources_and_readbacks_are_pinned(self):
        data = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in data[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
