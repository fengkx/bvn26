"""Retain the live target fact without converting temporal order into causation."""
import json
import unittest
from pathlib import Path
from analyze import validate_combined_bytes
from channels import validate_channels

HERE = Path(__file__).resolve().parent

class LiveTests(unittest.TestCase):
    def test_raw_target_and_no_join(self):
        run = HERE / 'run-01'
        tag = json.loads((HERE / 'build.json').read_text())['run_id']
        data = [(run / name).read_bytes() for name in ['flashlog.prelaunch.log',
                'flashlog.input-baseline.log', 'flashlog.after.log', 'combined.log', 'tagged.log']]
        validate_combined_bytes(*data, tag)
        counts, targets = validate_channels(data[0], data[3], tag)
        self.assertEqual(counts, {'root': 8124, 'side': 1, 'literal': 1, 'target': 1})
        self.assertEqual(targets[0]['owner'], '/game/p1/mc')
        self.assertEqual(targets[0]['frame'], 174)
        self.assertFalse(targets[0]['initiating_call_join_proven'])
        self.assertFalse(targets[0]['helper_lifetime_proven'])

    def test_structural_and_continuation_refusals_retained(self):
        report = json.loads((HERE / 'observations.json').read_text())
        self.assertEqual(report['structural_refusal'], 'Incomplete actor state at clock boundary')
        self.assertEqual(len(report['incomplete_clock_boundaries']), 10)
        self.assertEqual(report['literal_analysis']['outcomes'][0]['classification'], 'literal-before-without-after')
        for name in ['continuation-breadcrumb', 'consumer-goto-after']:
            self.assertEqual(report['counts'].get(name, 0), 0)
        self.assertEqual(report['side_counts'], {'before': 1})
        self.assertEqual(report['literal_counts'], {'before': 1})
        for flag in ['production_admitted', 'native_parity_proven', 'oracle_accepted',
                     'certified_global_tick', 'os_input_join_proven']:
            self.assertIs(report[flag], False)
