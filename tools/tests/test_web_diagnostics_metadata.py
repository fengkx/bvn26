from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_web_diagnostics_metadata as metadata  # noqa: E402


class WebDiagnosticsMetadataTests(unittest.TestCase):
    def test_embedded_identity_excludes_itself_and_finalize_hashes_exported_pck(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "godot"
            (project / "generated").mkdir(parents=True)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            (project / "generated" / "fighter.json").write_text('{"id":"sakura"}\n', encoding="utf-8")
            template = root / "web-template.zip"
            template.write_bytes(b"fixed-template")
            common = {
                "git_commit": "a" * 40,
                "dirty_paths": ["godot/web/shell.html"],
                "template_sha256": metadata.sha256_file(template),
                "engine_version": "4.7.2",
                "built_at": "2026-09-15T00:00:00Z",
            }

            first = metadata.prepare_metadata(project, **common)
            metadata.write_json(project / metadata.METADATA_RELATIVE_PATH, first)
            second = metadata.prepare_metadata(project, **common)
            self.assertEqual(first["buildID"], second["buildID"])
            self.assertEqual(first["sourceTreeSha256"], second["sourceTreeSha256"])

            pck = root / "game.pck"
            pck.write_bytes(b"exported artifact bytes")
            sidecar_path = root / "build-metadata.json"
            sidecar = metadata.finalize_metadata(project / metadata.METADATA_RELATIVE_PATH, pck)
            metadata.write_json(sidecar_path, sidecar)
            loaded = json.loads(sidecar_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["buildID"], first["buildID"])
            self.assertEqual(loaded["pckSha256"], metadata.sha256_file(pck))
            self.assertEqual(loaded["pckHashKind"], "exported_artifact")

    def test_dirty_paths_only_include_changes_copied_into_export_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "godot"
            (source / "generated").mkdir(parents=True)
            (source / "project.godot").write_text("base\n", encoding="utf-8")
            (source / "fighter_runtime.gd").write_text("base runtime\n", encoding="utf-8")
            (source / "timeline_preview.gd").write_text("base timeline\n", encoding="utf-8")
            self._git(root, "init", "-q")
            self._git(root, "config", "user.email", "test@example.invalid")
            self._git(root, "config", "user.name", "Test")
            self._git(root, "add", "godot")
            self._git(root, "commit", "-qm", "fixture")

            packaged = root / "packaged-godot"
            shutil.copytree(source, packaged)
            (source / "fighter_runtime.gd").write_text("changed runtime\n", encoding="utf-8")
            (source / "timeline_preview.gd").write_text("parallel unshipped change\n", encoding="utf-8")
            (source / "new_test.gd").write_text("shipped test\n", encoding="utf-8")
            shutil.copy2(source / "fighter_runtime.gd", packaged / "fighter_runtime.gd")
            shutil.copy2(source / "new_test.gd", packaged / "new_test.gd")
            (packaged / "generated" / "texture.png.import").write_text("generated\n", encoding="utf-8")
            (packaged / "generated" / ".DS_Store").write_bytes(b"desktop metadata")

            paths = metadata.discover_included_dirty_paths(root, source, packaged)
            self.assertEqual(paths, ["godot/fighter_runtime.gd", "godot/new_test.gd"])

    def test_staged_source_can_be_used_without_reading_live_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            source = root / "godot"
            source.mkdir(parents=True)
            (source / "project.godot").write_text("committed\n", encoding="utf-8")
            self._git(root, "init", "-q")
            self._git(root, "config", "user.email", "test@example.invalid")
            self._git(root, "config", "user.name", "Test")
            self._git(root, "add", "godot")
            self._git(root, "commit", "-qm", "fixture")

            staged_project = Path(temporary) / "snapshot" / "godot"
            staged_project.mkdir(parents=True)
            (staged_project / "project.godot").write_text("committed\n", encoding="utf-8")
            (source / "project.godot").write_text("changed after snapshot\n", encoding="utf-8")

            paths = metadata.discover_included_dirty_paths(
                root,
                staged_project,
                staged_project,
                git_project_path=Path("godot"),
            )
            self.assertEqual(paths, [])

            (source / "project.godot").write_text("committed\n", encoding="utf-8")
            (staged_project / "project.godot").write_text("captured dirty snapshot\n", encoding="utf-8")
            paths = metadata.discover_included_dirty_paths(
                root,
                staged_project,
                staged_project,
                git_project_path=Path("godot"),
            )
            self.assertEqual(paths, ["godot/project.godot"])

    def test_prepare_uses_vercel_commit_when_git_metadata_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            root.mkdir()
            project = Path(temporary) / "snapshot" / "godot"
            (project / "generated").mkdir(parents=True)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            template = Path(temporary) / "web-template.zip"
            template.write_bytes(b"template")
            commit = "b" * 40
            arguments = [
                "build_web_diagnostics_metadata.py",
                "prepare",
                "--repo",
                str(root),
                "--source-project",
                str(project),
                "--project",
                str(project),
                "--git-project-path",
                "godot",
                "--template",
                str(template),
                "--engine-version",
                "4.7.2",
            ]

            with patch.object(sys, "argv", arguments), patch.dict(
                os.environ, {"VERCEL_GIT_COMMIT_SHA": commit}
            ):
                self.assertEqual(metadata.main(), 0)

            embedded = json.loads((project / "generated/build_metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(embedded["gitCommit"], commit)
            self.assertEqual(embedded["dirtyPaths"], [])

    def test_missing_git_and_vercel_commit_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "non-empty git commit"):
                metadata.git_commit(root)

    def test_preflight_reports_vercel_remediation_without_git(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = os.environ.copy()
            environment.pop("VERCEL_GIT_COMMIT_SHA", None)
            command = [sys.executable, str(ROOT / "tools/build_web_diagnostics_metadata.py"),
                       "preflight", "--repo", temporary]
            missing = subprocess.run(command, env=environment, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 1)
            self.assertIn("Automatically expose System Environment Variables", missing.stderr)
            self.assertNotIn("Traceback", missing.stderr)
            environment["VERCEL_GIT_COMMIT_SHA"] = "d" * 40
            present = subprocess.run(command, env=environment, capture_output=True, text=True)
            self.assertEqual(present.returncode, 0, present.stderr)
            self.assertIn("gitCommit=" + "d" * 40, present.stdout)

    def test_git_checkout_takes_precedence_over_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._git(root, "init", "-q")
            self._git(root, "-c", "user.email=test@example.invalid", "-c", "user.name=Test",
                      "commit", "--allow-empty", "-qm", "fixture")
            expected = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            self.assertEqual(metadata.git_commit(root, vercel_fallback="d" * 40), expected)

    def test_finalize_failure_removes_existing_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "godot"
            project.mkdir()
            embedded = project / "build_metadata.json"
            embedded.write_text(
                json.dumps({"schemaVersion": 1, "buildID": "a" * 64, "gitCommit": "b" * 40}),
                encoding="utf-8",
            )
            output = root / "build-metadata.json"
            output.write_text('{"old":"metadata"}\n', encoding="utf-8")
            arguments = [
                "build_web_diagnostics_metadata.py",
                "finalize",
                "--embedded",
                str(embedded),
                "--pck",
                str(root / "missing.pck"),
                "--output",
                str(output),
            ]

            with patch.object(sys, "argv", arguments):
                with self.assertRaisesRegex(ValueError, "missing or empty"):
                    metadata.main()
            self.assertFalse(output.exists())

    @staticmethod
    def _git(root: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
