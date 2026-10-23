from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/importer'))
import prepare_form_graph
from form_profile_guard import package_hashes


class PrepareFormGraphTests(unittest.TestCase):
    def setUp(self):
        self.base = ROOT / 'godot/generated/fighters/daitu'
        self.target = ROOT / 'godot/generated/forms/daitu-2'

    def test_source_checked_dry_run_does_not_activate_or_rewrite(self):
        before = [package_hashes(p) for p in (self.base, self.target)]
        manifest = (self.base / 'form_profiles.json').read_bytes()
        result = prepare_form_graph.prepare(self.base, {2: self.target})
        self.assertFalse(result['written'])
        self.assertEqual(set(result['contract']['nodes']), {'1', '2'})
        self.assertEqual(before, [package_hashes(p) for p in (self.base, self.target)])
        self.assertEqual(manifest, (self.base / 'form_profiles.json').read_bytes())

    def test_late_target_compile_failure_preserves_entire_installed_graph(self):
        before = [package_hashes(p) for p in (self.base, self.target)]
        manifest = (self.base / 'form_profiles.json').read_bytes()
        compile_programs = prepare_form_graph.compile_programs
        calls = []

        def fail_target(directory, bundle, timeline):
            calls.append(timeline['sprite_id'])
            if len(calls) == 2:
                raise ValueError('target.swf:frame_9: uncompiled call')
            compile_programs(directory, bundle, timeline)

        with patch.object(prepare_form_graph, 'compile_programs', fail_target):
            with self.assertRaisesRegex(ValueError, 'target.swf:frame_9'):
                prepare_form_graph.prepare(self.base, {2: self.target}, write_outputs=True)
        self.assertEqual(calls, [458, 1138])
        self.assertEqual(before, [package_hashes(p) for p in (self.base, self.target)])
        self.assertEqual(manifest, (self.base / 'form_profiles.json').read_bytes())

    def test_target_cannot_escape_production_forms(self):
        with self.assertRaisesRegex(ValueError, 'Invalid parent frame/production target'):
            prepare_form_graph.prepare(self.base, {2: ROOT / 'godot/tests'})

    def test_publication_io_failure_restores_all_installed_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installed, staged = {}, {}
            for frame in (1, 2):
                for mapping, label in ((installed, 'installed'), (staged, 'staged')):
                    directory = root / label / str(frame)
                    for name in ('ai_controller', 'player_controller'):
                        (directory / name).mkdir(parents=True)
                        (directory / name / 'body.gd').write_text(f'{label} body {frame}')
                    (directory / 'ai.json').write_text(f'{label} AI {frame}')
                    mapping[frame] = directory
            (installed[1] / 'form_profiles.json').write_text('reviewed old activation')
            (staged[1] / 'form_profiles.json').write_text('new activation')
            # The new file must disappear again if a later node cannot publish.
            (staged[1] / 'player_controller' / 'new.gd').write_text('new method')
            (installed[1] / 'ai_controller' / 'body.gd').unlink()
            (installed[1] / 'ai_controller').rmdir()
            before = {p.relative_to(root): p.read_bytes() for p in (root / 'installed').rglob('*') if p.is_file()}
            replace = os.replace
            failed = False

            def fail_second_node(source, destination):
                nonlocal failed
                if Path(destination) == installed[2] / 'ai.json' and not failed:
                    failed = True
                    raise OSError('injected target publication failure')
                return replace(source, destination)

            with patch.object(prepare_form_graph.os, 'replace', fail_second_node):
                with self.assertRaisesRegex(OSError, 'target publication failure'):
                    prepare_form_graph.publish_programs(staged, installed)
            after = {p.relative_to(root): p.read_bytes() for p in (root / 'installed').rglob('*') if p.is_file()}
            self.assertTrue(failed)
            self.assertEqual(before, after)
