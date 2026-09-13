"""Dynamic captures must verify the SWF at the fighterDir embedded in main.swf."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'probes'))
import capture_native_player as capture


class RuntimeFighterPreflightTests(unittest.TestCase):
    def make_build(self, root, actual_root, expected_bytes):
        build = Path(root) / 'build'
        (build / 'game').mkdir(parents=True)
        actual = Path(actual_root) / 'game/fighter/Sakura.swf'
        actual.parent.mkdir(parents=True, exist_ok=True)
        actual.write_bytes(expected_bytes)
        body = b'file://' + str(actual.parent).encode() + b'/'
        main = b'CWS\x09\x00\x00\x00\x00' + zlib.compress(body)
        (build / 'game/main.swf').write_bytes(main)
        (build / 'build.json').write_text(json.dumps({
            'run_id': 'runtime-fighter-test',
            'dynamic_move_case': True,
            'move_case': {'slot': 'p1'},
            'configuration': {'p1': '樱'},
            'outputs_sha256': {
                'game/fighter/Sakura.swf': hashlib.sha256(expected_bytes).hexdigest()
            },
        }))
        return build

    def test_embedded_runtime_fighter_hash_matches_expected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build = self.make_build(root, root / 'runtime', b'marked-fighter')
            result = capture._verify_runtime_fighter(
                build, json.loads((build / 'build.json').read_text()))
        self.assertEqual(result['sha256'], hashlib.sha256(b'marked-fighter').hexdigest())
        self.assertEqual(result['path'], str(root / 'runtime/game/fighter/Sakura.swf'))

    def test_copied_candidate_fails_when_main_still_loads_unmarked_base(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build = self.make_build(root / 'candidate', root / 'base', b'original-fighter')
            (build / 'game/fighter').mkdir(parents=True)
            (build / 'game/fighter/Sakura.swf').write_bytes(b'marked-fighter')
            metadata = json.loads((build / 'build.json').read_text())
            metadata['outputs_sha256']['game/fighter/Sakura.swf'] = hashlib.sha256(
                b'marked-fighter').hexdigest()
            (build / 'build.json').write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, 'Runtime fighter hash mismatch'):
                capture._verify_runtime_fighter(build, metadata)

    def test_declared_build_artifact_must_match_its_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build = self.make_build(root, root / 'runtime', b'marked-fighter')
            (build / 'game/fighter').mkdir(parents=True)
            (build / 'game/fighter/Sakura.swf').write_bytes(b'wrong-candidate')
            with self.assertRaisesRegex(ValueError, 'Build artifact hash mismatch'):
                capture._verify_runtime_fighter(
                    build, json.loads((build / 'build.json').read_text()))


if __name__ == '__main__':
    unittest.main()
