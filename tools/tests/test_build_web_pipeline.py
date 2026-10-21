from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class WebBuildPipelineTests(unittest.TestCase):
    def test_vercel_upload_keeps_build_dependencies(self) -> None:
        required = [
            "tools/build_web.sh",
            "tools/bind_web_export_template.py",
            "tools/build_web_diagnostics_metadata.py",
            "tools/run_godot_checked.py",
            "tools/build_online_manifest.py",
            "tools/test_online_manifest.py",
            "tools/test_online_lobby_ui.py",
            "tools/tests/test_web_diagnostics_metadata.py",
            "tools/importer/visual_blend_modes.py",
            "services/matchmaking/src/protocol.ts",
            "services/matchmaking/src/catalog.json",
            "godot/project.godot",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            upload = Path(temporary)
            subprocess.run(["git", "init", "--quiet", str(upload)], check=True)
            # Vercel uses gitignore-style rules. Check the upload boundary,
            # before the build script copies files into its isolated stage.
            shutil.copy2(ROOT / ".vercelignore", upload / ".gitignore")
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "--stdin"],
                cwd=upload, input="\n".join(required) + "\n",
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "")
            excluded = subprocess.run(
                ["git", "check-ignore", "--no-index", "--stdin"],
                cwd=upload, input="tools/importer/extract_timeline_geometry.py\n",
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(excluded.returncode, 0, excluded.stderr)

    def test_failed_preflight_removes_stale_sidecar_and_cleans_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            repo = sandbox / "repo"
            tools = repo / "tools"
            test_tools = tools / "tests"
            output = repo / "dist/web"
            build_tmp = sandbox / "tmp"
            test_tools.mkdir(parents=True)
            output.mkdir(parents=True)
            build_tmp.mkdir()
            shutil.copy2(ROOT / "tools/build_web.sh", tools / "build_web.sh")
            shutil.copy2(
                ROOT / "tools/build_web_diagnostics_metadata.py",
                tools / "build_web_diagnostics_metadata.py",
            )
            shutil.copy2(
                ROOT / "tools/tests/test_web_diagnostics_metadata.py",
                test_tools / "test_web_diagnostics_metadata.py",
            )
            (output / "build-metadata.json").write_text('{"old":"sidecar"}\n', encoding="utf-8")

            fake_godot = sandbox / "godot"
            fake_godot.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"${1:-}\" == \"--version\" ]]; then\n"
                "  printf '%s\\n' '4.7.2.stable.official'\n"
                "  exit 0\n"
                "fi\n"
                "exit 99\n",
                encoding="utf-8",
            )
            fake_godot.chmod(0o755)
            environment = os.environ.copy()
            environment.pop("VERCEL_GIT_COMMIT_SHA", None)
            environment.update(
                {
                    "GODOT_BIN": str(fake_godot),
                    "TEMPLATE_DIR": str(sandbox / "missing-templates"),
                    "TMPDIR": str(build_tmp),
                }
            )

            missing_commit = subprocess.run(
                ["bash", str(tools / "build_web.sh")], cwd=repo, env=environment,
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(missing_commit.returncode, 1)
            self.assertIn("WEB_BUILD_PROVENANCE_ERROR", missing_commit.stderr)
            self.assertNotIn("Web build raw logs:", missing_commit.stdout)
            self.assertFalse(output.joinpath("build-metadata.json").exists())
            self.assertFalse(any(path.name.startswith("bvn26-web-build.") for path in build_tmp.iterdir()))

            environment["VERCEL_GIT_COMMIT_SHA"] = "c" * 40
            (output / "build-metadata.json").write_text('{"old":"sidecar"}\n', encoding="utf-8")
            result = subprocess.run(
                ["bash", str(tools / "build_web.sh")],
                cwd=repo,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("template is missing or empty", result.stderr)
            self.assertFalse(output.joinpath("build-metadata.json").exists())
            self.assertFalse(any(path.name.startswith("bvn26-web-build.") for path in build_tmp.iterdir()))

    def test_release_template_hash_is_for_template_bound_to_preset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            template = root / "template bundle" / "web_nothreads_release.zip"
            template.parent.mkdir()
            template.write_bytes(b"selected Web release template")
            preset = root / "export_presets.cfg"
            preset.write_text(
                '[preset.0]\nname="Web"\nplatform="Web"\n\n'
                '[preset.0.options]\ncustom_template/debug=""\ncustom_template/release=""\n',
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "tools/bind_web_export_template.py"),
                    "--preset",
                    str(preset),
                    "--template",
                    str(template),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            bound_path = str(template.resolve())
            self.assertIn(f'custom_template/release="{bound_path}"', preset.read_text(encoding="utf-8"))
            self.assertIn(f"sha256={hashlib.sha256(template.read_bytes()).hexdigest()}", result.stdout)

    def test_only_exact_macos_ca_error_pair_is_reported_as_environment_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wrapper = ROOT / "tools/run_godot_checked.py"
            known_log = root / "known.log"
            known_script = (
                "print(" + repr('ERROR: Condition "ret != noErr" is true. Returning: ""') + ")\n"
                "print(" + repr("   at: get_system_ca_certificates (platform/macos/os_macos.mm:1035)") + ")"
            )
            known_output = subprocess.run(
                [
                    "python3",
                    str(wrapper),
                    "--log",
                    str(known_log),
                    "--",
                    "python3",
                    "-c",
                    known_script,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(known_output.returncode, 0, known_output.stdout + known_output.stderr)
            self.assertIn("GODOT_ENV_WARNING", known_output.stderr)
            self.assertIn("get_system_ca_certificates", known_output.stderr)
            self.assertIn("get_system_ca_certificates", known_log.read_text(encoding="utf-8"))

            near_miss_log = root / "near-miss.log"
            near_miss_script = (
                "print(" + repr('ERROR: Condition "ret != noErr" is true. Returning: ""') + ")\n"
                "print('unrelated line')\n"
                "print(" + repr("   at: get_system_ca_certificates (platform/macos/os_macos.mm:1035)") + ")"
            )
            near_miss_output = subprocess.run(
                [
                    "python3",
                    str(wrapper),
                    "--log",
                    str(near_miss_log),
                    "--",
                    "python3",
                    "-c",
                    near_miss_script,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(near_miss_output.returncode, 0)
            self.assertIn("GODOT_LOG_SCAN_FAIL", near_miss_output.stderr)

            unknown_log = root / "unknown.log"
            unknown_output = subprocess.run(
                [
                    "python3",
                    str(wrapper),
                    "--log",
                    str(unknown_log),
                    "--",
                    "python3",
                    "-c",
                    "print('ERROR: Unexpected project error')",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(unknown_output.returncode, 0)
            self.assertIn("GODOT_LOG_SCAN_FAIL", unknown_output.stderr)
            self.assertIn("Unexpected project error", unknown_output.stderr)

    def test_script_error_with_zero_exit_fails_and_removes_sidecar(self) -> None:
        self._run_import_pipeline(fail_import=True)

    def test_import_generated_files_are_in_final_export_manifest(self) -> None:
        self._run_import_pipeline(fail_import=False)

    def test_export_input_drift_prevents_publishing(self) -> None:
        self._run_import_pipeline(fail_import=False, mutate_export=True)

    def _run_import_pipeline(self, *, fail_import: bool, mutate_export: bool = False) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sandbox = Path(temporary)
            repo = sandbox / "repo"
            tools = repo / "tools"
            test_tools = tools / "tests"
            output = repo / "dist/web"
            build_tmp = sandbox / "tmp"
            (repo / "godot/generated/main/character_selection").mkdir(parents=True)
            (repo / "godot/generated/stages/catalog").mkdir(parents=True)
            (repo / "godot/generated/stages/current_world").mkdir(parents=True)
            (repo / "godot/generated/music").mkdir(parents=True)
            (repo / "godot/generated/effects").mkdir(parents=True)
            (repo / "godot/web").mkdir(parents=True)
            test_tools.mkdir(parents=True)
            (repo / "services/matchmaking/src").mkdir(parents=True)
            output.mkdir(parents=True)
            build_tmp.mkdir()
            for name in (
                "project.godot",
                "main.tscn",
                "render_surface.tscn",
                "export_presets.cfg",
            ):
                (repo / "godot" / name).write_text("fixture\n", encoding="utf-8")
            (repo / "godot/export_presets.cfg").write_text(
                '[preset.0]\nname="Web"\nplatform="Web"\n\n'
                '[preset.0.options]\ncustom_template/debug=""\ncustom_template/release=""\n',
                encoding="utf-8",
            )
            (repo / "godot/web/shell.html").write_text("<html></html>\n", encoding="utf-8")
            (repo / "godot/generated/main/character_selection/available.json").write_text(
                '{"fighters": {}, "helpers": {}}\n', encoding="utf-8"
            )
            (repo / "godot/generated/stages/catalog/catalog.json").write_text(
                '{"stages": []}\n', encoding="utf-8"
            )
            (repo / "godot/generated/stages/current_world/timeline.json").write_text(
                "{}\n", encoding="utf-8"
            )
            (repo / "godot/generated/music/music.json").write_text("{}\n", encoding="utf-8")
            (repo / "services/matchmaking/src/protocol.ts").write_text(
                "export const VERSION = 1;\n", encoding="utf-8"
            )
            (repo / "services/matchmaking/src/catalog.json").write_text(
                '{"fighters": [], "helpers": [], "stages": []}\n', encoding="utf-8"
            )
            for name in (
                "build_web.sh",
                "bind_web_export_template.py",
                "build_web_diagnostics_metadata.py",
                "run_godot_checked.py",
                "build_online_manifest.py",
                "test_online_manifest.py",
                "test_online_lobby_ui.py",
            ):
                shutil.copy2(ROOT / "tools" / name, tools / name)
            (tools / "importer").mkdir()
            shutil.copy2(
                ROOT / "tools/importer/visual_blend_modes.py",
                tools / "importer/visual_blend_modes.py",
            )
            shutil.copy2(
                ROOT / "tools/tests/test_web_diagnostics_metadata.py",
                test_tools / "test_web_diagnostics_metadata.py",
            )
            (output / "build-metadata.json").write_text('{"old":"sidecar"}\n', encoding="utf-8")

            template_dir = sandbox / "templates"
            template_dir.mkdir()
            (template_dir / "web_nothreads_release.zip").write_bytes(b"fake template")
            fake_godot = sandbox / "godot-bin"
            fake_godot.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"${1:-}\" == \"--version\" ]]; then\n"
                "  printf '%s\\n' '4.7.2.stable.official'\n"
                "  exit 0\n"
                "fi\n"
                "project_path=''\n"
                "expect_path=0\n"
                "for argument in \"$@\"; do\n"
                "  if [[ \"$expect_path\" == 1 ]]; then project_path=\"$argument\"; expect_path=0; continue; fi\n"
                "  if [[ \"$argument\" == '--path' ]]; then expect_path=1; fi\n"
                "done\n"
                "if ! grep -Fqx \"custom_template/release=\\\"${EXPECTED_WEB_TEMPLATE}\\\"\" \"$project_path/export_presets.cfg\"; then\n"
                "  printf '%s\\n' 'release template was not bound to the hashed template'\n"
                "  exit 88\n"
                "fi\n"
                "printf '%s\\n' 'SCRIPT ERROR: Parse Error: simulated import failure'\n"
                "exit 0\n",
                encoding="utf-8",
            )
            if not fail_import:
                # This fixture tests build orchestration, not lobby behavior.
                (tools / "test_online_lobby_ui.py").write_text("print('LOBBY_FIXTURE_OK')\n")
                fake_godot.write_text(textwrap.dedent("""\
                    #!/usr/bin/env python3
                    import hashlib, json, os, sys
                    from pathlib import Path
                    args = sys.argv[1:]
                    if '--version' in args:
                        print('4.7.2.stable.official')
                        sys.exit(0)
                    project = Path(args[args.index('--path') + 1])
                    if '--import' in args:
                        (project / 'generated/music/track.mp3.import').write_text('generated import settings')
                    elif '--export-release' in args:
                        manifest = json.loads((project / 'generated/online/manifest.json').read_text())
                        inputs = json.loads((project.parent / 'evidence/online/manifest-inputs.json').read_text())
                        assert manifest['compatibility'] == inputs['compatibility']
                        record = next(r for r in inputs['inputs']['content'] if r['path'].endswith('track.mp3.import'))
                        assert record['sha256'] == hashlib.sha256(b'generated import settings').hexdigest()
                        embedded = json.loads((project / 'generated/build_metadata.json').read_text())
                        import build_web_diagnostics_metadata as metadata
                        assert embedded['sourceTreeSha256'] == metadata.sha256_tree(project, exclude={metadata.METADATA_RELATIVE_PATH})
                        output = Path(args[args.index('--export-release') + 2])
                        for suffix in ['.html', '.js', '.wasm', '.pck']:
                            output.with_suffix(suffix).write_bytes(b'exported fixture')
                        if os.environ.get('FIXTURE_MUTATE_EXPORT') == '1':
                            (project / 'generated/music/track.mp3.import').write_text('changed during export')
                    """), encoding="utf-8")
            fake_godot.chmod(0o755)
            environment = os.environ.copy()
            environment.update(
                {
                    "GODOT_BIN": str(fake_godot),
                    "TEMPLATE_DIR": str(template_dir),
                    "TMPDIR": str(build_tmp),
                    "VERCEL_GIT_COMMIT_SHA": "c" * 40,
                    "EXPECTED_WEB_TEMPLATE": str((template_dir / "web_nothreads_release.zip").resolve()),
                    "PYTHONPATH": str(tools),
                    "FIXTURE_MUTATE_EXPORT": "1" if mutate_export else "0",
                }
            )

            # Existing metadata does not guarantee that Git can read HEAD.
            (repo / ".git").mkdir()
            result = subprocess.run(
                ["bash", str(tools / "build_web.sh")],
                cwd=repo,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            if not fail_import:
                if mutate_export:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("stale online compatibility output", result.stderr)
                    self.assertFalse(output.joinpath("build-metadata.json").exists())
                    self.assertFalse(output.joinpath("index.pck").exists())
                    return
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("WEB_BUILD_METADATA_OK", result.stdout)
                sidecar = json.loads((output / "build-metadata.json").read_text())
                self.assertEqual(sidecar["pckSha256"], hashlib.sha256(b"exported fixture").hexdigest())
                self.assertFalse(any(path.name.startswith("bvn26-web-build.") for path in build_tmp.iterdir()))
                return

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("GODOT_LOG_SCAN_FAIL", result.stderr)
            self.assertIn("SCRIPT ERROR: Parse Error", result.stderr)
            self.assertFalse(output.joinpath("build-metadata.json").exists())
            self.assertFalse(any(path.name.startswith("bvn26-web-build.") for path in build_tmp.iterdir()))
            logs = list((build_tmp / "bvn26-web-build-logs").glob("*/import.log"))
            self.assertEqual(len(logs), 1)
            self.assertIn("SCRIPT ERROR: Parse Error", logs[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
