from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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

            paths = metadata.discover_included_dirty_paths(root, source, packaged)
            self.assertEqual(paths, ["godot/fighter_runtime.gd", "godot/new_test.gd"])

    @staticmethod
    def _git(root: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
