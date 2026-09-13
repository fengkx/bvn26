import os
import tempfile
import unittest
from pathlib import Path

from tools.test_move_cases import resolve_cli_paths


class MoveCasesPathTests(unittest.TestCase):
    def test_cli_paths_are_anchored_to_calling_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            previous = Path.cwd()
            try:
                os.chdir(root)
                actual = resolve_cli_paths(Path('bin/godot'), Path('fixtures'), Path('results'))
            finally:
                os.chdir(previous)
        self.assertEqual(actual, tuple((root / name).resolve() for name in ('bin/godot', 'fixtures', 'results')))


if __name__ == '__main__':
    unittest.main()
