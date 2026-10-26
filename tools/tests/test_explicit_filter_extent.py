import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_explicit_filter_extent import report

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r64'


class ExplicitFilterExtentTests(unittest.TestCase):
    def test_explicit_success_cannot_admit_implicit_cache(self):
        result = report(EVIDENCE / 'native')
        self.assertTrue(result['explicit_gpu_passed'])
        self.assertEqual(sum(v['exact'] for v in result['explicit_gpu']['scores'].values()), 19200)
        self.assertFalse(result['implicit_equivalence_passed'])
        self.assertFalse(result['passed'])
        self.assertFalse(result['production_admitted'])
        for stage in ('input', 'filtered'):
            self.assertEqual(result['implicit_vs_explicit'][stage]['exact'], 6400)
        self.assertEqual(result['implicit_vs_explicit']['final']['exact'], 6392)
        self.assertEqual(len(result['implicit_vs_explicit']['final']['failures']), 8)

    def test_sources_native_and_pinned_gpu_readbacks_unchanged(self):
        provenance = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', EVIDENCE / 'native'),
                          ('output_sha256', EVIDENCE)]:
            for name, digest in provenance[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
