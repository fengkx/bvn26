import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.analyze_shadow_crossed_parameters import analyze, decode

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r78'


class ShadowCrossedParameterTests(unittest.TestCase):
    def test_crossed_controls_reject_composition_without_regressing_phase(self):
        result = analyze(EVIDENCE / 'native')
        self.assertEqual(result, json.loads(gzip.decompress((EVIDENCE / 'analysis.json.gz').read_bytes())))
        self.assertFalse(result['bounded_cpu_passed'])
        self.assertFalse(result['production_admitted'])
        self.assertEqual({k: v['exact'] for k, v in result['scores'].items()},
                         {'input': 207360, 'blur': 207360, 'filtered': 190396, 'requested_alpha_control': 181008})
        for score in result['phase_regressions'].values():
            self.assertEqual(score['exact'], score['cases'])
        unit = [p for p in result['partitions'] if p['filter_alpha'] == p['strength'] == 1]
        self.assertEqual(len(unit), 5)
        for part in unit:
            self.assertEqual(part['samples'], 4608)
            self.assertEqual(part['exact'], 4492 if part['distance'] == -0.501953125 else 4608)

    def test_alpha_byte_quantization_is_explicitly_read_back(self):
        cases = decode(EVIDENCE / 'native')
        self.assertEqual(cases[0]['key'][5], 0.5)
        self.assertEqual(cases[0]['key'][12], 0.498039215686275)
        self.assertEqual(cases[0]['observed_alpha_byte'], 127)
        self.assertEqual(cases[3]['key'][5], 0.75)
        self.assertEqual(cases[3]['key'][12], 0.749019607843137)
        self.assertEqual(cases[3]['observed_alpha_byte'], 191)

    def test_native_sources_and_old_phase_controls_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, base in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((base / name).read_bytes()).hexdigest(), digest)
