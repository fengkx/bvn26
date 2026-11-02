"""Reject static/executed conflation and malformed target windows."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s288', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ContinuationBoundaryTests(unittest.TestCase):
    def test_static_sites_and_retained_observations_are_not_execution(self):
        report = audit.diagnose()
        self.assertEqual(report['historical']['events'], 9493)
        self.assertEqual([r['post'] for r in report['historical']['controls']], ['1', '0'])
        self.assertTrue(report['historical_cpu_entry_stop'])
        self.assertEqual(report['historical_resolver_locations'], 0)
        self.assertTrue(all(v is None for v in report['observations'].values()))
        for key in ('production_admitted', 'native_parity_proven', 'exact_continuation_proved'):
            self.assertIs(report[key], False)
        for site in report['static_sites'].values():
            rows = site['instructions']
            self.assertTrue(all(a['end'] == b['offset'] for a, b in zip(rows, rows[1:])))
            self.assertIn('NOT loaded', site['coordinates'])
            self.assertGreater(rows[0]['offset'], site['definition']['body_offset'])
            self.assertEqual(rows[-1]['hex'], '4f')

    def test_changed_pop_and_register_are_rejected(self):
        prior = audit.load_prior()
        with tarfile.open(HERE.parent / 's266/build-extension.tar.gz') as package:
            raw = package.extractfile('game/main.swf').read()
        site = audit.windows(raw, 60000, prior.CONTROL_SEQUENCE)
        data, _, _ = audit.action_block(raw, 60000)
        for row, relative, replacement in ((site['instructions'][5], 0, 0x04),
                                            (site['instructions'][6], 4, 5)):
            changed = bytearray(data)
            changed[:3] = b'FWS'
            changed[row['offset'] + relative] = replacement
            with self.assertRaisesRegex(ValueError, 'missing or ambiguous'):
                audit.windows(bytes(changed), 60000, prior.CONTROL_SEQUENCE)

    def test_invalid_swf_length_rejected(self):
        with self.assertRaisesRegex(ValueError, 'length mismatch'):
            audit.action_block(b'FWS\x08\x09\0\0\0', 16)

    def test_both_requirements_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            for flag in ('--require-native-continuation', '--require-retained-activation'):
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'), '--output',
                                         str(Path(directory) / 'report.json'), flag],
                                        cwd=audit.ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn('S288_NATIVE_CONTINUATION_UNPROVED', result.stderr)


if __name__ == '__main__':
    unittest.main()
