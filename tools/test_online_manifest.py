#!/usr/bin/env python3
"""Check online fingerprint determinism, drift detection and input filtering."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("build_online_manifest.py")
SPEC = importlib.util.spec_from_file_location("build_online_manifest", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
manifest_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest_tool)


class OnlineManifestTests(unittest.TestCase):
    def test_changed_runtime_file_changes_its_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "runtime.gd"
            source.write_text("extends Node\n", encoding="utf-8")
            first_records = manifest_tool.records([source], base=root)
            first = manifest_tool.fingerprint(first_records, {"engine": "test"})

            source.write_text("extends Node\nvar online := true\n", encoding="utf-8")
            second_records = manifest_tool.records([source], base=root)
            second = manifest_tool.fingerprint(second_records, {"engine": "test"})
            self.assertNotEqual(first, second)

    def test_build_fingerprint_changes_when_engine_or_protocol_changes(self) -> None:
        records = [{"path": "godot/main.gd", "sha256": "a" * 64, "size": 1}]
        baseline = manifest_tool.fingerprint(records, {"engine": "4.7.2", "protocol": 1})
        self.assertNotEqual(
            baseline,
            manifest_tool.fingerprint(records, {"engine": "4.8.0", "protocol": 1}),
        )
        self.assertNotEqual(
            baseline,
            manifest_tool.fingerprint(records, {"engine": "4.7.2", "protocol": 2}),
        )

    def test_runtime_file_scan_omits_editor_and_temporary_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "fighter.bin").write_bytes(b"runtime")
            (root / ".DS_Store").write_bytes(b"desktop metadata")
            (root / "._fighter.bin").write_bytes(b"AppleDouble metadata")
            (root / "fighter.bin.tmp").write_bytes(b"temporary")
            cache = root / ".godot" / "imported"
            cache.mkdir(parents=True)
            (cache / "cache.bin").write_bytes(b"cache")

            included = {path.relative_to(root).as_posix() for path in manifest_tool.files_under(root)}
            self.assertEqual(included, {"fighter.bin"})

    def test_manifest_does_not_hash_its_own_output(self) -> None:
        build_paths = {path.resolve() for path in manifest_tool.build_inputs()}
        content_paths, _roster = manifest_tool.content_inputs()
        content_paths = {path.resolve() for path in content_paths}
        output = manifest_tool.OUTPUT.resolve()
        self.assertNotIn(output, build_paths)
        self.assertNotIn(output, content_paths)

    def test_build_and_content_changes_have_independent_fingerprints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_file = root / "runtime.gd"
            content_file = root / "music.json"
            protocol_file = root / "protocol.ts"
            build_file.write_text("extends Node\n", encoding="utf-8")
            content_file.write_text('{"track":"a.mp3"}\n', encoding="utf-8")
            protocol_file.write_text("export const VERSION = 1;\n", encoding="utf-8")
            roster = {"fighters": ["fighter"], "helpers": ["helper"], "stages": ["stage"]}
            original_records = manifest_tool.records

            def local_records(paths, base=manifest_tool.ROOT):
                return original_records(paths, base=root)

            with (
                patch.object(manifest_tool, "MATCHMAKING_PROTOCOL", protocol_file),
                patch.object(manifest_tool, "GODOT", root),
                patch.object(manifest_tool, "build_inputs", return_value=[build_file]),
                patch.object(manifest_tool, "content_inputs", return_value=([content_file], roster)),
                patch.object(manifest_tool, "records", side_effect=local_records),
            ):
                initial, _ = manifest_tool.make_documents()
                build_file.write_text("extends Node\nvar changed := true\n", encoding="utf-8")
                build_changed, _ = manifest_tool.make_documents()
                self.assertNotEqual(
                    initial["compatibility"]["build"],
                    build_changed["compatibility"]["build"],
                )
                self.assertEqual(
                    initial["compatibility"]["content"],
                    build_changed["compatibility"]["content"],
                )
                content_file.write_text('{"track":"b.mp3"}\n', encoding="utf-8")
                content_changed, _ = manifest_tool.make_documents()
                self.assertEqual(
                    build_changed["compatibility"]["build"],
                    content_changed["compatibility"]["build"],
                )
                self.assertNotEqual(
                    build_changed["compatibility"]["content"],
                    content_changed["compatibility"]["content"],
                )

    def test_runtime_content_inputs_include_music_catalog_and_default_stage(self) -> None:
        paths, _roster = manifest_tool.content_inputs()
        included = {path.resolve() for path in paths}
        self.assertIn((manifest_tool.GODOT / "generated/music/music.json").resolve(), included)
        self.assertIn((manifest_tool.GODOT / "generated/stages/current_world/timeline.json").resolve(), included)

    def test_online_ui_font_metadata_covers_static_non_ascii_strings(self) -> None:
        font_metadata_path = manifest_tool.GODOT / "generated/main/title_menu/font.json"
        if not font_metadata_path.exists():
            self.skipTest("menu font has not been regenerated from the licensed source")
        metadata = json.loads(font_metadata_path.read_text(encoding="utf-8"))
        covered = set(metadata["characters"])
        for path in (manifest_tool.GODOT / "title_menu.gd", manifest_tool.GODOT / "online_lobby.gd"):
            required = {character for character in path.read_text(encoding="utf-8") if ord(character) > 127}
            self.assertTrue(required.issubset(covered), f"{path.name} has uncovered UI characters: {''.join(sorted(required - covered))}")


if __name__ == "__main__":
    unittest.main()
