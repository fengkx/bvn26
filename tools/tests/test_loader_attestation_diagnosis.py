"""Loader evidence must not turn artifact provenance into instance identity."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evidence/sampling-upgrade/s268'


class LoaderAttestationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('s268_diagnose', HERE / 'diagnose.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.report = cls.module.diagnose()

    def test_retained_evidence_recomputes(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        self.assertEqual([r['events'] for r in self.report['runs'].values()], [5503, 5416, 9774])

    def test_matching_archived_bytes_do_not_attest_instance(self):
        for run in self.report['runs'].values():
            self.assertTrue(run['archived_output_and_receipt_hashes_match'])
            for key in ('actual_load_callback_target', 'consumed_bytes_observation',
                        'callback_to_instance_lifetime'):
                self.assertIsNone(run[key])
        self.assertFalse(self.report['loader_attestation_proved'])
        self.assertFalse(self.report['production_admitted'])
        self.assertFalse(self.report['native_parity_proven'])

    def test_helper_request_is_not_complete_callback(self):
        for run in self.report['runs'].values():
            self.assertTrue(run['loader_sites']['helper_load_before_request'])
            self.assertFalse(run['loader_sites']['callback_consumes_target'])
            self.assertEqual(run['event_kind_counts']['helper_load'], 2)

    def test_wrong_resource_negative_is_offline_only(self):
        control = self.report['wrong_resource_negative']
        self.assertNotEqual(control['expected_sha256'], control['substituted_sha256'])
        self.assertEqual(control['wrong_bytes_exit'], 1)
        self.assertFalse(control['actual_wrong_resource_load_performed'])
        self.assertIsNone(control['runtime_wrong_resource_control'])
        with self.assertRaisesRegex(ValueError, 'wrong resource bytes'):
            self.module.check_bytes(b'different bytes', control['expected_sha256'])

    def test_changed_callback_cannot_reuse_source_conclusion(self):
        sites = self.report['source_sites']
        source = sites['request'] + '\n' + sites['callback']
        with self.assertRaisesRegex(ValueError, 'changed loader source sites'):
            self.module.loader_sites(source.replace('loadStep++;', 'target.removeMovieClip();'))

    def test_strict_requirement_fails_on_real_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-m',
                                     'evidence.sampling-upgrade.s268.diagnose',
                                     '--output', str(Path(directory) / 'report.json'),
                                     '--require-loader-attestation'], cwd=ROOT,
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('LOADER_ATTESTATION_UNPROVED', result.stdout)


if __name__ == '__main__':
    unittest.main()
