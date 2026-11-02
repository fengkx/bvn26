"""Protect cursor ambiguity, retained invocation separation, and fail-closed gates."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('s295', HERE / 'diagnose.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ResolverBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.diagnose()
        cls.site = json.loads((HERE.parent / 's288/diagnosis.json').read_text())['static_sites']['authored_control']

    def test_archive_cursor_hypotheses_are_ambiguous(self):
        worker = self.report['retained_worker']
        rows = worker['cursor_candidates']
        self.assertEqual([r['current_body_relative'] for r in rows], [118, 119, 138])
        self.assertEqual([r['next_body_relative'] for r in rows], [119, 120, 139])
        self.assertEqual(rows[0]['next_opcode_file_offset'], rows[1]['current_opcode_file_offset'])
        self.assertEqual(worker['ambiguous_file_offset'], 589408)
        self.assertEqual(worker['body_occurrences_in_archived_swf'], 1)
        self.assertEqual(audit.sha(bytes.fromhex(worker['body_hex'])), worker['definition']['body_sha256'])

    def test_retained_post_does_not_identify_activation(self):
        controls = self.report['historical']['controls']
        self.assertEqual([(r['mode'], r['post']) for r in controls], [('retain', '1'), ('remove', '0')])
        self.assertEqual(self.report['historical']['events'], 9493)
        self.assertIsNone(self.report['observations']['retained_activation'])
        self.assertTrue(all(value is None for value in self.report['observations'].values()))
        self.assertTrue(self.report['locked_s288_reproduced'])

    def test_no_production_or_other_rank_admission(self):
        self.assertEqual(self.report['scope'], 'AFTER-s290 rank #5 only')
        for key in ('production_admitted', 'native_parity_proven', 'exact_continuation_proved'):
            self.assertIs(self.report[key], False)
        for key in ('new_builds', 'new_player_launches', 'new_captures', 'product_obligations_closed'):
            self.assertEqual(self.report[key], 0)
        self.assertEqual(len(self.report['exclusions']), 5)

    def test_gap_rejected(self):
        site = copy.deepcopy(self.site)
        site['instructions'][5]['offset'] += 1
        with self.assertRaisesRegex(ValueError, 'noncontiguous'):
            audit.cursor_candidates(site)

    def test_wrong_opcode_rejected(self):
        site = copy.deepcopy(self.site)
        site['instructions'][5]['hex'] = '04'
        with self.assertRaisesRegex(ValueError, 'unexpected instruction bytes'):
            audit.cursor_candidates(site)

    def test_missing_boundary_rejected(self):
        site = copy.deepcopy(self.site)
        site['instructions'][-1]['instruction'] = None
        with self.assertRaisesRegex(ValueError, 'missing three'):
            audit.cursor_candidates(site)

    def test_input_tampering_rejected(self):
        original = Path.read_bytes
        def changed(path):
            raw = original(path)
            return raw + b'changed' if path == HERE / 'cursor-symbols.txt' else raw
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'locked input changed'):
                audit.diagnose()

    def test_all_gates_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            for gate, code in audit.GATES.items():
                output = Path(directory) / 'report.json'
                result = subprocess.run([sys.executable, str(HERE / 'diagnose.py'),
                    '--output', str(output), '--require-' + gate], cwd=audit.ROOT,
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(code, result.stderr)
                self.assertFalse(json.loads(output.read_text())['gates'][gate]['proved'])


if __name__ == '__main__':
    unittest.main()
