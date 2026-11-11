"""Reject cross-instance, stale and ambiguous native movie bindings."""
import copy
import unittest
from pathlib import Path
from capture_observer import bound_window


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {'frontmost_pid': 42, 'applications': [{
            'pid': 42, 'executable': '/player', 'ax_windows_error': 0,
            'ax_windows': [{'title': '/unique/main.swf', 'title_error': 0}],
            'cg_windows': [{'kCGWindowOwnerPID': 42, 'kCGWindowName': '/unique/main.swf',
                            'kCGWindowBounds': {'Width': 600, 'Height': 428},
                            'kCGWindowIsOnscreen': True}]}]}

    def bind(self):
        return bound_window(self.snapshot, 42, Path('/player'), Path('/unique/main.swf'), True)

    def test_other_same_bundle_process_cannot_replace_owned_pid(self):
        other = copy.deepcopy(self.snapshot['applications'][0])
        other['pid'] = 43
        self.snapshot['applications'] = [other]
        with self.assertRaisesRegex(ValueError, 'PID'):
            self.bind()

    def test_accepts_one_exact_owned_window_with_unrelated_peer(self):
        self.snapshot['applications'].append({'pid': 43, 'executable': '/player'})
        self.assertEqual(self.bind()['kCGWindowOwnerPID'], 42)

    def test_rejects_duplicate_movie_windows(self):
        app = self.snapshot['applications'][0]
        app['cg_windows'].append(copy.deepcopy(app['cg_windows'][0]))
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            self.bind()

    def test_rejects_foreign_window_owner(self):
        self.snapshot['applications'][0]['cg_windows'][0]['kCGWindowOwnerPID'] = 43
        with self.assertRaises(ValueError):
            self.bind()

    def test_rejects_title_and_ax_failure(self):
        for key, value in [('ax_windows', []), ('ax_windows_error', -25211)]:
            with self.subTest(key=key):
                before = copy.deepcopy(self.snapshot)
                self.snapshot['applications'][0][key] = value
                with self.assertRaisesRegex(ValueError, 'AX'):
                    self.bind()
                self.snapshot = before

    def test_rejects_focus_loss_and_offscreen(self):
        self.snapshot['frontmost_pid'] = 43
        with self.assertRaisesRegex(ValueError, 'frontmost'):
            self.bind()
        self.snapshot['frontmost_pid'] = 42
        self.snapshot['applications'][0]['cg_windows'][0]['kCGWindowIsOnscreen'] = False
        with self.assertRaisesRegex(ValueError, 'visible'):
            self.bind()


if __name__ == '__main__':
    unittest.main()
