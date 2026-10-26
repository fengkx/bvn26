import gzip
import hashlib
import json
from pathlib import Path
import unittest
from tools.probes.run_grouped_family_gpu import cases, compare

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/importer-loud-fail/r77/render'


class GroupedFamilyGpuTests(unittest.TestCase):
    def test_all_actual_family_stages_match_native(self):
        rows = json.loads(gzip.decompress((EVIDENCE / 'rows.json.gz').read_bytes()))
        report = compare(cases(), rows)
        self.assertTrue(report['passed'])
        self.assertFalse(report['production_admitted'])
        self.assertEqual(set(report['scores']), {'input', 'blur', 'filtered', 'final_copy'})
        for score in report['scores'].values():
            self.assertEqual((score['exact'], score['samples'], score['failures']), (69120, 69120, []))
        rows[0]['family'] = 1
        with self.assertRaisesRegex(ValueError, 'Family/blur'):
            compare(cases(), rows)

    def test_native_sources_and_clean_batches_are_pinned(self):
        p = json.loads((EVIDENCE / 'provenance.json').read_text())
        for key, root in [('source_sha256', ROOT), ('native_sha256', ROOT), ('readback_sha256', EVIDENCE)]:
            for name, digest in p[key].items():
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)
        logs = list((EVIDENCE / 'batches').glob('*/godot.log'))
        self.assertEqual(len(logs), 12)
        for log in logs:
            data = json.loads(log.with_name('fixture.json').read_text())
            self.assertNotIn('ERROR', log.read_text())
            self.assertIn(f"GROUPED_FAMILY_ROWS_OK cases={len(data['cases'])} production_admitted=false", log.read_text())
