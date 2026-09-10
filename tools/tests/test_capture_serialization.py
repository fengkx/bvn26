"""Independent probe batches must not truncate each other's global Flash log."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'probes'))
import capture_native_player as capture


class CaptureSerializationTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
