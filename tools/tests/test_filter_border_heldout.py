import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_filter_border_heldout import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r66'


class FilterBorderHeldoutTests(unittest.TestCase):
    def test_fixed_border_is_rejected_without_changing_arithmetic(self):
        r = analyze(EVIDENCE / 'native')
        self.assertEqual(r['scores']['filtered']['exact'], 40320)
        self.assertEqual(r['scores']['declared_model']['exact'], 40320)
        self.assertEqual(r['scores']['final']['exact'], 40236)
        self.assertEqual({v['key'][4] for v in r['scores']['final']['failures']}, {4, 8})
        self.assertFalse(r['right_border_hypothesis_passed'])
        self.assertFalse(r['implicit_extent_model_admitted'])
        self.assertFalse(r['production_admitted'])
        self.assertEqual(r['measured_padding'], {'2':[2], '3':[2], '4':[2], '6':[4], '7':[4], '8':[4], '9':[5]})

    def test_sources_and_native_counterexamples_are_pinned(self):
        provenance = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', EVIDENCE / 'native'),
                          ('output_sha256', EVIDENCE)]:
            for name, digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
