"""Protect native boot custody and refusal before launch on a busy capture lock."""
import fcntl
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('oracle_boot', HERE / 'capture_boot.py')
boot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boot)


class BootSafetyTests(unittest.TestCase):
    def test_asset_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'main.swf').write_bytes(b'original')
            hashes = {'main.swf': boot.sha(b'original')}
            boot.verify_assets(root, hashes)
            (root / 'main.swf').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                boot.verify_assets(root, hashes)

    def test_append_interval_never_infers_attribution(self):
        self.assertEqual(boot.appended_bytes(b'prior', b'priornew'), b'new')
        self.assertEqual(boot.appended_bytes(b'prior', b'prior'), b'')
        for changed in (b'', b'rotated', b'prioXnew'):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                boot.appended_bytes(b'prior', changed)

    def test_busy_shared_lock_refuses_before_preflight_or_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'game').mkdir()
            (root / 'game/main.swf').write_bytes(b'fixture-original')
            (root / 'manifest.json').write_text(json.dumps({'file_sha256': {'game/main.swf': boot.sha(b'fixture-original')}}))
            (root / 'tools/probes').mkdir(parents=True)
            config = b'ErrorReportingEnable=1\nTraceOutputFileEnable=1\n'
            (root / 'tools/probes/mm.cfg').write_bytes(config)
            (root / 'mm.cfg').write_bytes(config)
            player = root / 'player'
            player.write_bytes(b'fixture-player')
            capture = boot.load_capture()
            with patch.object(boot, 'ROOT', root), patch.object(boot, 'PLAYER_SHA', boot.sha(b'fixture-player')), \
                    patch.object(boot, 'load_capture', return_value=capture), \
                    patch.object(capture, 'player_binary', return_value=player), \
                    patch.object(capture, 'LOCK_PATH', root / 'lock'), \
                    patch.object(capture, 'preflight') as preflight, \
                    patch.object(Path, 'home', return_value=root), \
                    patch.object(boot.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='fixture', stderr='')), \
                    patch.object(boot.subprocess, 'Popen') as launch:
                with (root / 'lock').open('a') as held:
                    fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.assertEqual(boot.run(root / 'output', 0.01), 1)
                launch.assert_not_called()
                preflight.assert_not_called()
            receipt = json.loads((root / 'output/session.json').read_text())
            self.assertEqual(receipt['error']['type'], 'BlockingIOError')
            self.assertFalse(receipt['oracle_accepted'])
            self.assertFalse(receipt['production_admitted'])
            self.assertNotIn('launch', receipt)

    def test_retained_attempt_is_not_a_replay(self):
        receipt = json.loads((HERE / 'attempt-02/session.json').read_text())
        self.assertFalse(receipt['oracle_accepted'])
        self.assertFalse(receipt['native_parity_proven'])
        for field in ('visible_content', 'input_target_binding', 'post_menu_state',
                      'fixed_input_tape', 'random_seed', 'random_tape', 'normalized_trace'):
            self.assertIsNone(receipt[field])
        self.assertEqual(receipt['input_events_sent'], 0)
        self.assertEqual(receipt['cleanup']['remaining_matching_pids'], [])
        delta = (HERE / 'attempt-02/flashlog.delta.log').read_bytes()
        self.assertEqual(len(delta), receipt['flashlog']['delta_size'])
        self.assertEqual(boot.sha(delta), receipt['flashlog']['delta_sha256'])
        self.assertEqual(receipt['source_sha256'], receipt['build']['outputs_sha256'])


if __name__ == '__main__':
    unittest.main()
