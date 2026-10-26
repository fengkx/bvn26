"""Exercise the real Web staging commands without downloads or Godot export."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class WebManifestStagingTests(unittest.TestCase):
    def test_manifest_imports_from_isolated_build_snapshot(self):
        script = (ROOT / 'tools/build_web.sh').read_text()
        start = script.index('for tool in build_online_manifest.py ')
        end = script.index('# Build and check compatibility fingerprints', start)
        with tempfile.TemporaryDirectory() as temporary:
            upload = Path(temporary) / 'upload'
            stage = Path(temporary) / 'snapshot'
            # This fixture has only explicitly included build files, not the
            # checkout's full importer package or Python's ambient search path.
            for line in (ROOT / '.vercelignore').read_text().splitlines():
                if line.startswith('!/') and not line.endswith('/'):
                    relative = line[2:]
                    source = ROOT / relative
                    self.assertTrue(source.is_file(), relative)
                    destination = upload / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, destination)
            (stage / 'tools').mkdir(parents=True)
            (stage / 'services/matchmaking/src').mkdir(parents=True)
            env = {**os.environ, 'ROOT_DIR': str(upload), 'STAGING_REPO': str(stage)}
            subprocess.run(['bash', '-euc', script[start:end]], env=env,
                           cwd=temporary, check=True, capture_output=True, text=True)
            result = subprocess.run(
                [sys.executable, '-E', '-B', str(stage / 'tools/build_online_manifest.py'), '--help'],
                cwd=temporary, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('usage:', result.stdout)


if __name__ == '__main__':
    unittest.main()
