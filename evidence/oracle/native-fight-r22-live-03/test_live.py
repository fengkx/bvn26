"""Keep the new raw live evidence fail-closed without manufacturing after events."""
import json
import unittest
from analyze import HERE, validate_combined_bytes

class LiveReceiptTests(unittest.TestCase):
    def test_raw_identity_and_freshness(self):
        run = HERE / 'run-01'
        names = ['flashlog.prelaunch.log', 'flashlog.input-baseline.log',
                 'flashlog.after.log', 'combined.log', 'tagged.log']
        data = [run.joinpath(name).read_bytes() for name in names]
        tag = json.loads((HERE / 'build.json').read_text())['run_id']
        validate_combined_bytes(*data, tag)
        with self.assertRaises(ValueError):
            validate_combined_bytes(*data[:3], data[3] + b'extra', data[4], tag)

    def test_after_silence_and_admission_refusal_retained(self):
        report = json.loads((HERE / 'observations.json').read_text())
        self.assertEqual(report['literal_counts'], {'before': 1})
        self.assertEqual(report['side_counts'], {'before': 1})
        self.assertEqual(len(report['incomplete_clock_boundaries']), 12)
        self.assertEqual(report['fight_key_positive'], 1)
        for flag in ['production_admitted', 'native_parity_proven', 'oracle_accepted',
                     'certified_global_tick', 'os_input_join_proven']:
            self.assertIs(report[flag], False)
        raw = (HERE / 'run-01/combined.log').read_bytes()
        tag = report['run_tag'].encode()
        prefix = b'M002LITERAL|' + tag + b'|doAllAction|'
        self.assertEqual(raw.count(prefix + b'before'), 1)
        self.assertEqual(raw.count(prefix + b'after'), 0)
