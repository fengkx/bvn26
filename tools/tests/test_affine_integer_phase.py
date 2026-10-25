import gzip
import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_affine_integer_phase import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r168'


class AffineIntegerPhaseTests(unittest.TestCase):
    def test_integer_phase_keeps_all_old_bounds_without_admission(self):
        r = analyze(EVIDENCE / 'native', ROOT / 'evidence/importer-loud-fail/r166/native')
        failures = {k: v.pop('failures') for k, v in r['scores'].items()}
        self.assertEqual(failures, json.loads(gzip.decompress((EVIDENCE / 'failures.json.gz').read_bytes())))
        self.assertEqual(r, json.loads((EVIDENCE / 'summary.json').read_text()))
        self.assertEqual(r['old_zero_phase'], {'samples': 30, 'exact': 30})
        self.assertTrue(all(v['joint_feasible'] and not v['nonmonotone_steps'] and len(v['other_channel_values']) == 1 for v in r['groups']))
        self.assertEqual(sum(v['exact'] for k, v in r['scores'].items() if k.endswith('/fixed_center')), 3370)
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
