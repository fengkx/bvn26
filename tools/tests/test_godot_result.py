import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.godot_result import process_succeeded
from tools import test_move_cases as moves

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_source_parity_suite as parity


class GodotResultTests(unittest.TestCase):
    def test_exit_marker_and_script_error_are_independent(self):
        for marker in ['MOVE_CASE_REFERENCE_OK', 'MOVE_CASE_BATCH_OK']:
            for code, log, expected in [
                (0, marker, True),
                (1, marker, False),
                (0, 'Godot Engine v4.7.2.stable.official\n', False),
                (0, 'SCRIPT ERROR: Assertion failed.\n' + marker, False),
                (0, marker + '\nSCRIPT ERROR: Parse Error', False),
                (0, 'ERROR: 2 resources still in use at exit.\n' + marker, True),
                (0, 'Parse Error\n' + marker, True),
            ]:
                with self.subTest(marker=marker, code=code, log=log):
                    self.assertEqual(process_succeeded(code, log, required_marker=marker), expected)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name)
        self.fixture = self.output / 'fixture.case.json'
        self.fixture.write_text(json.dumps({'id': 'fixture', 'frames': 0, 'slot': 'p1'}))
        self.rows = [{'slot': 'p1', 'frame': 1}, {'slot': 'p2', 'frame': 1}]

    def test_single_case_still_requires_complete_trace(self):
        target = self.output / 'fixture.case.json'
        # The executor derives its output from the fixture stem, so keep inputs separate.
        fixtures = self.output / 'inputs'
        fixtures.mkdir()
        fixture = fixtures / self.fixture.name
        fixture.write_bytes(self.fixture.read_bytes())
        for rows, expected in [(self.rows, True), (self.rows[:1], False)]:
            target.write_text(json.dumps(rows))
            run = subprocess.CompletedProcess([], 0, 'MOVE_CASE_REFERENCE_OK', '')
            with patch.object(moves.subprocess, 'run', return_value=run):
                self.assertEqual(moves.execute(Path('/godot'), fixture, self.output)['executed'], expected)

    def test_batch_still_requires_per_case_marker_and_complete_trace(self):
        for rows, suffix, expected in [
            (self.rows, 'MOVE_CASE_REFERENCE_OK fixture', True),
            (self.rows, 'MOVE_CASE_REFERENCE_OK other', False),
            (self.rows[:1], 'MOVE_CASE_REFERENCE_OK fixture', False),
        ]:
            (self.output / 'fixture.json').write_text(json.dumps(rows))
            run = subprocess.CompletedProcess([], 0, 'MOVE_CASE_BATCH_OK\n' + suffix, '')
            with patch.object(moves.subprocess, 'run', return_value=run):
                result = moves.execute_batch(Path('/godot'), [self.fixture], self.output)
            self.assertEqual(result[0]['executed'], expected)

    def test_move_timeouts_keep_existing_result_shapes(self):
        with patch.object(moves.subprocess, 'run', side_effect=subprocess.TimeoutExpired('godot', 45)):
            self.assertEqual(moves.execute(Path('/godot'), self.fixture, self.output),
                             {'id': 'fixture', 'executed': False, 'status': 'timeout'})
            result = moves.execute_batch(Path('/godot'), [self.fixture], self.output)
        self.assertFalse(result[0]['executed'])
        self.assertEqual(result[0]['status'], 'failed')

    def test_archive_runner_keeps_marker_policy_and_timeout_propagation(self):
        def unpack(_suite, output):
            cases = output / 'cases'
            cases.mkdir()
            (cases / 'fixture.json').write_text('{}')
            return {'cases': []}

        for number, log, expected in [(0, 'MOVE_CASE_BATCH_OK', 0),
                                      (1, 'MOVE_CASE_REFERENCE_OK', 1),
                                      (2, 'MOVE_CASE_BATCH_OK\nSCRIPT ERROR: Assertion failed.', 1)]:
            output = self.output / str(number)
            argv = ['suite', '--suite', '/unused.tar.gz', '--output', str(output), '--godot', '/godot']
            run = subprocess.CompletedProcess([], 0, log, '')
            with patch.object(sys, 'argv', argv), patch.object(parity, 'unpack', side_effect=unpack), \
                    patch.object(parity.subprocess, 'run', return_value=run), self.assertRaises(SystemExit) as exit:
                parity.main()
            self.assertEqual(exit.exception.code, expected)
            self.assertEqual(json.loads((output / 'comparison.json').read_text())['execution'][0]['passed'], expected == 0)
        argv = ['suite', '--suite', '/unused.tar.gz', '--output', str(self.output / 'timeout'), '--godot', '/godot']
        with patch.object(sys, 'argv', argv), patch.object(parity, 'unpack', side_effect=unpack), \
                patch.object(parity.subprocess, 'run', side_effect=subprocess.TimeoutExpired('godot', 3600)), \
                self.assertRaises(subprocess.TimeoutExpired):
            parity.main()


if __name__ == '__main__':
    unittest.main()
