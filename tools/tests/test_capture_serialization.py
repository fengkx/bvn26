"""Independent probe batches must not truncate each other's global Flash log."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'probes'))
import capture_native_player as capture


class CaptureSerializationTests(unittest.TestCase):
    @staticmethod
    def _build(directory):
        build = Path(directory) / 'build'
        (build / 'game').mkdir(parents=True)
        (build / 'game' / 'main.swf').write_bytes(b'fixture')
        (build / 'build.json').write_text('{"run_id":"fault-injection"}\n')
        return build

    def test_log_ownership_spans_the_whole_capture(self):
        active = 0
        maximum = 0
        entered = threading.Event()

        def run(*_args):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            entered.set()
            time.sleep(0.05)
            active -= 1
            return True

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(capture, 'LOCK_PATH', Path(directory) / 'lock'), patch.object(capture, '_capture_locked', run):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    first = pool.submit(capture.capture, None, None, None)
                    self.assertTrue(entered.wait(1))
                    second = pool.submit(capture.capture, None, None, None)
                    self.assertTrue(first.result())
                    self.assertTrue(second.result())
        self.assertEqual(maximum, 1)

    def test_busy_lock_fails_before_player_operations(self):
        calls = 0

        def run(*_args):
            nonlocal calls
            calls += 1
            return True

        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / 'lock'
            with patch.object(capture, 'LOCK_PATH', lock_path), patch.object(
                capture, 'LOCK_WAIT_SECONDS', 0.05
            ), patch.object(capture, '_capture_locked', run):
                with lock_path.open('a') as lock:
                    import fcntl
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    with self.assertRaises(TimeoutError):
                        capture.capture(None, None, None)
        self.assertEqual(calls, 0)

    def test_snapshot_error_still_terminates_launcher(self):
        process = MagicMock()
        process.poll.return_value = None
        snapshot_error = OSError('snapshot destination failed')
        with tempfile.TemporaryDirectory() as directory:
            build = self._build(directory)
            destination = Path(directory) / 'capture.log'
            with patch.object(capture, 'LOG', Path(directory) / 'flashlog.txt'), patch.object(
                capture, 'matching_players', return_value=set()
            ), patch.object(capture.subprocess, 'Popen', return_value=process), patch.object(
                Path, 'write_bytes', side_effect=snapshot_error
            ):
                with self.assertRaises(OSError) as raised:
                    capture._capture_locked(build, destination, 0)
                self.assertIs(raised.exception, snapshot_error)
        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5)

    def test_process_scan_error_still_terminates_launcher_and_preserves_error(self):
        process = MagicMock()
        process.poll.return_value = None
        scan_error = RuntimeError('ps failed')
        with tempfile.TemporaryDirectory() as directory:
            build = self._build(directory)
            destination = Path(directory) / 'capture.log'
            with patch.object(capture, 'LOG', Path(directory) / 'flashlog.txt'), patch.object(
                capture, 'matching_players', side_effect=[set(), scan_error]
            ), patch.object(capture.subprocess, 'Popen', return_value=process):
                with self.assertRaises(RuntimeError) as raised:
                    capture._capture_locked(build, destination, 0)
                self.assertIs(raised.exception, scan_error)
        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5)

    def test_kill_error_still_terminates_launcher_and_preserves_error(self):
        process = MagicMock()
        process.poll.return_value = None
        kill_error = PermissionError('player belongs to another owner')
        with tempfile.TemporaryDirectory() as directory:
            build = self._build(directory)
            destination = Path(directory) / 'capture.log'
            with patch.object(capture, 'LOG', Path(directory) / 'flashlog.txt'), patch.object(
                capture, 'matching_players', side_effect=[set(), {4242}]
            ), patch.object(capture.subprocess, 'Popen', return_value=process), patch.object(
                capture.os, 'kill', side_effect=kill_error
            ):
                with self.assertRaises(PermissionError) as raised:
                    capture._capture_locked(build, destination, 0)
                self.assertIs(raised.exception, kill_error)
        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5)

    def test_capture_error_is_primary_when_cleanup_also_fails(self):
        process = MagicMock()
        process.poll.return_value = None
        capture_error = ValueError('malformed trace line')
        snapshot_error = OSError('snapshot destination failed')
        scan_error = RuntimeError('ps failed')
        log = MagicMock()
        # The preflight duplicate-run check must pass; fail while collecting
        # the launched player's log so cleanup is exercised with a primary error.
        log.exists.side_effect = [False, True]
        log.read_bytes.side_effect = capture_error
        with tempfile.TemporaryDirectory() as directory:
            build = self._build(directory)
            destination = Path(directory) / 'capture.log'
            with patch.object(capture, 'LOG', log), patch.object(
                capture, 'matching_players', side_effect=[set(), scan_error]
            ), patch.object(capture.subprocess, 'Popen', return_value=process), patch.object(
                Path, 'write_bytes', side_effect=snapshot_error
            ):
                with self.assertRaises(ValueError) as raised:
                    capture._capture_locked(build, destination, 0.01)
                self.assertIs(raised.exception, capture_error)
                self.assertIn('snapshot destination failed', '\n'.join(raised.exception.__notes__))
                self.assertIn('ps failed', '\n'.join(raised.exception.__notes__))
        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5)

    def test_wait_timeout_kills_launcher_then_waits_again(self):
        process = MagicMock()
        process.poll.return_value = None
        process.wait.side_effect = [
            subprocess.TimeoutExpired(cmd='open', timeout=5),
            None,
        ]
        with tempfile.TemporaryDirectory() as directory:
            build = self._build(directory)
            destination = Path(directory) / 'capture.log'
            with patch.object(capture, 'LOG', Path(directory) / 'flashlog.txt'), patch.object(
                capture, 'matching_players', return_value=set()
            ), patch.object(capture.subprocess, 'Popen', return_value=process):
                self.assertFalse(capture._capture_locked(build, destination, 0))
        process.kill.assert_called_once_with()
        self.assertEqual(process.wait.call_count, 2)

    def test_wait_timeout_still_reaps_when_kill_fails(self):
        process = MagicMock()
        process.poll.return_value = None
        process.wait.side_effect = [
            subprocess.TimeoutExpired(cmd='open', timeout=5),
            None,
        ]
        kill_error = PermissionError('launcher kill denied')
        process.kill.side_effect = kill_error
        with tempfile.TemporaryDirectory() as directory:
            build = self._build(directory)
            destination = Path(directory) / 'capture.log'
            with patch.object(capture, 'LOG', Path(directory) / 'flashlog.txt'), patch.object(
                capture, 'matching_players', return_value=set()
            ), patch.object(capture.subprocess, 'Popen', return_value=process):
                with self.assertRaises(PermissionError) as raised:
                    capture._capture_locked(build, destination, 0)
                self.assertIs(raised.exception, kill_error)
        process.kill.assert_called_once_with()
        self.assertEqual(process.wait.call_count, 2)


if __name__ == '__main__':
    unittest.main()
