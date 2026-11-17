"""Scoped matching must not promote missing evidence or full acceptance."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import audit_move_acceptance as module


class TargetedMoveAuditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        catalog = root / 'godot/generated/fighters/fixture/combat.json'
        catalog.parent.mkdir(parents=True)
        catalog.write_text(json.dumps({'command_catalog': {'entries': [], 'cancel_windows': []}}))
        self.root_patch = patch.object(module, 'ROOT', root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.case = {'id': 'case', 'fighter': 'fixture', 'label': 'attack',
                     'scenario': 'normal', 'target_frames': [10, 20]}
        self.native = {'id': 'case', 'executed': True}
        self.original = {'id': 'case', 'status': 'matched', 'target_seen': True}

    def test_matching_scope_preserves_full_acceptance_boundaries(self):
        result = module.audit([self.case], [self.native], [self.original])
        self.assertEqual(result['targeted_status'], 'targeted_cases_matched')
        self.assertEqual(result['targeted_unmatched_cases'], [])
        self.assertEqual(result['status'], 'not_accepted')
        self.assertEqual(result['full_acceptance'], 'not_accepted')
        self.assertTrue(result['additional_required_boundaries'])

    def test_empty_scope_does_not_pass(self):
        self.assertEqual(module.audit([], [], [])['targeted_status'], 'not_accepted')

    def test_missing_failed_or_unexercised_evidence_does_not_pass(self):
        for native, original in [([], [self.original]), ([self.native], []),
                                 ([dict(self.native, executed=False)], [self.original]),
                                 ([self.native], [dict(self.original, status='mismatch')]),
                                 ([self.native], [dict(self.original, target_seen=False)])]:
            with self.subTest(native=native, original=original):
                result = module.audit([self.case], native, original)
                self.assertEqual(result['targeted_status'], 'not_accepted')
                self.assertEqual(result['targeted_unmatched_cases'], ['case'])

    def test_negative_and_missing_label_cases_keep_separate_counts(self):
        for case, status in [(dict(self.case, scenario='energy_below'), 'matched_negative_case'),
                             (dict(self.case, target_frames=[None, None]), 'matched_source_missing_label')]:
            result = module.audit([case], [self.native], [dict(self.original, target_seen=False)])
            self.assertEqual(result['targeted_status'], 'targeted_cases_matched')
            self.assertEqual(result['case_counts'], {status: 1})


if __name__ == '__main__':
    unittest.main()
