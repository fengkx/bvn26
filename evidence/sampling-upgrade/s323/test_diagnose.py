"""Protect source applicability boundaries and honest proof failures."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s323', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.diagnose()
        cls.channel = cls.report['new_observer_applicability_audit']

    def test_saved_report_and_retained_proof(self):
        self.assertEqual(self.report, json.loads((HERE / 'diagnosis.json').read_text()))
        prior = json.loads((HERE.parent / 's314/diagnosis.json').read_text())
        retained = self.report['retained_validation_not_new_progress']
        self.assertEqual(retained['runs'], prior['runs'])
        self.assertEqual(retained['channel_audit'], prior['channel_audit'])
        self.assertTrue(retained['independent_pair_proved_and_closed'])

    def test_schedule_wraps_assignment_not_callback(self):
        schedule = self.channel['schedule']
        self.assertTrue(schedule['original_callback_preserved'])
        self.assertIn(',enter,', schedule['prefix'])
        self.assertIn(',exit,', schedule['suffix'])
        self.assertIn('_root.aiEvent', schedule['prefix'])
        self.assertIn('_root.aiEvent', schedule['suffix'])
        self.assertFalse(schedule['applied_to_player'])

    def test_selection_does_not_include_root_closure(self):
        self.assertEqual(self.channel['doaction']['target_kind'], 'DoAction')
        self.assertFalse(self.channel['doaction']['target_instrumented'])
        self.assertFalse(self.channel['callsite']['target_selected'])
        self.assertTrue(self.channel['doaction']['output_unchanged'])
        self.assertTrue(self.channel['callsite']['output_unchanged'])

    def test_body_exit_is_after_inner_call(self):
        source = self.channel['body_callback']['source']
        self.assertIn('name in fighter_sources', source)
        self.assertIn("call = '   on_enterframe();'", source)
        self.assertIn("+ call + '\\n_root.aiEvent(\"body_callback_exit\"", source)

    def test_no_live_proof_or_inventory(self):
        for name in ('production_admitted', 'native_parity_proven', 'independent_channel_proved',
                     'logger_replacement_survival_proved', 'callback_completion_proved',
                     'terminal_completeness_proved', 'terminal_inventory_executed',
                     'other_ranks_executed', 'full_as_proven'):
            self.assertIs(self.report[name], False)
        self.assertEqual(self.report['independently_observed_live_invocations'], [])
        self.assertIsNone(self.report['fixed_suffix_threshold'])
        for requirement in self.report['qualification_requirements'].values():
            self.assertIsNone(requirement['qualified_witness'])
        self.assertIsNone(self.channel['replacement_dependency']['independent_survival_witness'])

    def test_callback_mutation_rejected(self):
        callback = json.loads((HERE.parent / 's304/diagnosis.json').read_text())['source_callback']
        with self.assertRaisesRegex(ValueError, 'callback source changed'):
            audit.audit_applicability(callback['source'].replace('return;', 'stop();'), callback['sha256'])

    def test_tool_and_prior_pin_mutations_rejected(self):
        original = Path.read_bytes
        for target in ('tools/probes/build_ai_reference.py',
                       'tools/probes/doaction_observer.py',
                       'tools/probes/callsite_observer.py',
                       'evidence/sampling-upgrade/s314/diagnosis.json'):
            def changed(path):
                data = original(path)
                return data + b'changed' if path == audit.ROOT / target else data
            with self.subTest(target=target), patch.object(Path, 'read_bytes', changed):
                with self.assertRaisesRegex(ValueError, 'locked input changed'):
                    audit.diagnose()

    def test_cli_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in (None, *audit.GATES):
                command = [sys.executable, str(HERE / 'diagnose.py'), '--output',
                           str(Path(directory) / 'report.json')]
                if name:
                    command.append('--require-' + name)
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1 if name else 0, result.stderr)
                if name:
                    self.assertIn(audit.GATES[name], result.stderr)
                    self.assertNotIn('EVIDENCE_INVALID', result.stderr)


if __name__ == '__main__':
    unittest.main()
