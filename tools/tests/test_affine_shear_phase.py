import hashlib
import json
from pathlib import Path
import unittest

from tools.probes.analyze_affine_shear_phase import analyze

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r169'


class AffineShearPhaseTests(unittest.TestCase):
    def test_axis_controls_preserve_old_bounds(self):
        r = analyze(EVIDENCE / 'native', ROOT / 'evidence/importer-loud-fail/r168/summary.json')
        self.assertEqual(r, json.loads((EVIDENCE / 'summary.json').read_text()))
        self.assertEqual(sum(v['exact'] for v in r['zero_phase_pairs']), 90112)
        self.assertEqual(r['zero_phase_scalar'], {'samples': 132, 'exact': 132})
        self.assertTrue(all(v['feasible'] and not v['nonmonotone_steps'] and len(v['other_channel_values']) == 1 for v in r['groups']))
        self.assertEqual(sum(v['old_joint_feasible'] is True for v in r['groups']), 24)
        self.assertFalse(r['affine_sampler_admitted'])
        self.assertFalse(r['production_admitted'])

    def test_provenance(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('evidence_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
