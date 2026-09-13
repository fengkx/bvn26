import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.test_move_references import assert_capture_identity, capture_template_for_case
from tools.probes.move_cases import encode_case


class CaptureIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.probe = self.root / 'probe'
        self.probe.mkdir()
        self.source = self.root / 'locked.swf'
        self.source.write_bytes(b'locked source')
        self.helper_one = self.root / 'game/fighter/fz/h1.swf'
        self.helper_two = self.root / 'game/fighter/fz/h2.swf'
        self.helper_one.parent.mkdir(parents=True)
        self.helper_one.write_bytes(b'helper one')
        self.helper_two.write_bytes(b'helper two')
        (self.probe / 'game').mkdir()
        (self.probe / 'game/main.swf').write_bytes(b'instrumented game')
        self.case = {
            'id': 'fixture-one', 'frames': 12, 'slot': 'p1', 'target_frames': [1, 2],
            'setup': {'p1': {'x': 30, 'energy': 100}, 'p2': {'x': 70, 'energy': 200}},
            'inputs': [],
            'p1_helper': 'helper-one', 'p2_helper': 'helper-two',
        }
        self.run_id = 'capture-fixture-one-abc123'
        self.fixture = encode_case(self.case, self.run_id)
        self.fixture_url = (self.probe / 'case.txt').as_uri()
        (self.probe / 'case.txt').write_text(self.fixture)
        instrumentation = f'_root.aiFixtureLoader.load("{self.fixture_url}");\n'
        (self.probe / 'instrumentation.diff').write_text(instrumentation)
        self.template = {
            'run_id': self.run_id,
            'frames_after_ready': 12,
            'move_case': self.case,
            'fixture_url': self.fixture_url,
            'sources_sha256': {
                'locked.swf': hashlib.sha256(self.source.read_bytes()).hexdigest(),
                'game/fighter/fz/h1.swf': hashlib.sha256(self.helper_one.read_bytes()).hexdigest(),
                'game/fighter/fz/h2.swf': hashlib.sha256(self.helper_two.read_bytes()).hexdigest(),
            },
            'helper_sources': {
                'p1': {'character_id': 'helper-one', 'asset': 'h1', 'url': 'h1.swf'},
                'p2': {'character_id': 'helper-two', 'asset': 'h2', 'url': 'h2.swf'},
            },
            'outputs_sha256': {'game/main.swf': hashlib.sha256(b'instrumented game').hexdigest()},
            'instrumentation_sha256': hashlib.sha256(instrumentation.encode()).hexdigest(),
        }
        self.manifest = {
            'file_sha256': self.template['sources_sha256'],
            'fighter_catalog': {
                'helper-one': {'fzurl': 'h1.swf'},
                'helper-two': {'fzurl': 'h2.swf'},
            },
        }
        (self.root / 'manifest.json').write_text(__import__('json').dumps(self.manifest))

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_matching_capture_inputs(self):
        original_root = __import__('tools.test_move_references', fromlist=['ROOT']).ROOT
        try:
            import tools.test_move_references as module
            module.ROOT = self.root
            assert_capture_identity(self.case, self.template, self.fixture, self.probe, self.manifest)
        finally:
            module.ROOT = original_root

    def test_rebinds_case_template_to_exact_new_loadvars_payload(self):
        from tools.probes.move_cases import encode_case
        changed_case = dict(self.case, id='fixture-two')
        changed_run_id = 'capture-fixture-two-def456'
        fixture = encode_case(changed_case, changed_run_id)
        stale = dict(self.template, run_id=changed_run_id, move_case=changed_case,
                     fixture_sha256=hashlib.sha256(self.fixture.encode()).hexdigest())
        capture_template = capture_template_for_case(stale, changed_run_id, changed_case, fixture)
        self.assertNotEqual(capture_template['fixture_sha256'], stale['fixture_sha256'])
        self.assertEqual(capture_template['fixture_sha256'], hashlib.sha256(fixture.encode()).hexdigest())
        original_root = __import__('tools.test_move_references', fromlist=['ROOT']).ROOT
        try:
            import tools.test_move_references as module
            module.ROOT = self.root
            assert_capture_identity(changed_case, capture_template, fixture, self.probe, self.manifest)
            with self.assertRaisesRegex(ValueError, 'URL hash mismatch'):
                assert_capture_identity(changed_case, stale, fixture, self.probe, self.manifest)
        finally:
            module.ROOT = original_root

    def test_rejects_run_id_and_frame_mismatch(self):
        original_root = __import__('tools.test_move_references', fromlist=['ROOT']).ROOT
        try:
            import tools.test_move_references as module
            module.ROOT = self.root
            with self.assertRaisesRegex(ValueError, 'run_id mismatch'):
                assert_capture_identity(self.case, dict(self.template, run_id='wrong'),
                                         self.fixture, self.probe, self.manifest)
            with self.assertRaisesRegex(ValueError, 'frame count mismatch'):
                assert_capture_identity(dict(self.case, frames=13), self.template,
                                         self.fixture, self.probe, self.manifest)
        finally:
            module.ROOT = original_root

    def test_rejects_changed_loadvars_window(self):
        original_root = __import__('tools.test_move_references', fromlist=['ROOT']).ROOT
        try:
            import tools.test_move_references as module
            module.ROOT = self.root
            tampered = self.fixture.replace('p1x=30', 'p1x=31')
            with self.assertRaisesRegex(ValueError, 'LoadVars URL'):
                assert_capture_identity(self.case, self.template, tampered, self.probe, self.manifest)
        finally:
            module.ROOT = original_root

    def test_rejects_swf_bound_to_a_different_fixture_path(self):
        import tools.test_move_references as module
        original_root = module.ROOT
        try:
            module.ROOT = self.root
            other_url = (self.root / 'other-case.txt').as_uri()
            (self.probe / 'instrumentation.diff').write_text(
                f'_root.aiFixtureLoader.load("{other_url}");\n')
            with self.assertRaisesRegex(ValueError, 'SWF LoadVars URL binds'):
                assert_capture_identity(self.case, self.template, self.fixture,
                                        self.probe, self.manifest)
        finally:
            module.ROOT = original_root

    def test_rejects_changed_source_or_instrumented_output(self):
        original_root = __import__('tools.test_move_references', fromlist=['ROOT']).ROOT
        try:
            import tools.test_move_references as module
            module.ROOT = self.root
            self.source.write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError, 'source differs from locked input'):
                assert_capture_identity(self.case, self.template, self.fixture, self.probe, self.manifest)
        finally:
            module.ROOT = original_root


if __name__ == '__main__':
    unittest.main()
