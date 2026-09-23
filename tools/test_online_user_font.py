#!/usr/bin/env python3
"""Verify dynamic user-text font coverage, source provenance and OFL packaging."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FONT_DIRECTORY = ROOT / "godot/generated/main/fonts"
FONT_PATH = FONT_DIRECTORY / "user-cjk.woff2"
LICENSE_PATH = FONT_DIRECTORY / "FONT-LICENSE.txt"
METADATA_PATH = FONT_DIRECTORY / "font.json"
STATIC_FONT_PATH = ROOT / "godot/generated/main/title_menu/menu-font.ttf"
LICENSE_MARKER = "SIL Open Font License, Version 1.1"
NON_LITERAL_SAMPLES = ("龘璟姍𠮷㐀", "繁體姓名")


class OnlineUserFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        cls.coverage = set(cls.metadata["coverage_characters"])

    def test_dynamic_font_covers_names_outside_static_source_literals(self) -> None:
        source_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                ROOT / "godot/generated/main/title_menu/controller.gd",
                ROOT / "godot/title_menu.gd",
                ROOT / "godot/online_lobby.gd",
            )
        )
        for sample in NON_LITERAL_SAMPLES:
            self.assertNotIn(sample, source_text)
            self.assertTrue(set(sample).issubset(self.coverage), f"dynamic font misses {sample!r}")

    def test_coverage_metadata_records_actual_source_cmap_scope(self) -> None:
        self.assertEqual(self.metadata["format"], "WOFF2")
        self.assertEqual(self.metadata["source_family"], "Sarasa UI SC")
        self.assertEqual(self.metadata["font_family"], "BVN Online CJK")
        self.assertEqual(self.metadata["included_codepoint_count"], len(self.coverage))
        self.assertGreater(self.metadata["source_cmap_codepoint_count"], len(self.coverage))
        self.assertGreater(len(self.metadata["codepoint_ranges"]), 0)
        self.assertIn("not full Unicode", self.metadata["coverage_limit"])
        self.assertIn("CJK extension", self.metadata["coverage_limit"])
        self.assertGreater(self.metadata["font_bytes"], 0)
        self.assertLess(self.metadata["font_bytes"], 8_000_000)

    def test_font_resource_hash_and_license_are_packaged(self) -> None:
        self.assertTrue(FONT_PATH.is_file())
        self.assertEqual(FONT_PATH.stat().st_size, self.metadata["font_bytes"])
        self.assertEqual(
            hashlib.sha256(FONT_PATH.read_bytes()).hexdigest(),
            self.metadata["font_sha256"],
        )
        self.assertIn(LICENSE_MARKER, LICENSE_PATH.read_text(encoding="utf-8"))
        self.assertNotEqual(
            self.metadata["source_sha256"],
            hashlib.sha256(STATIC_FONT_PATH.read_bytes()).hexdigest(),
            "metadata must point to the TTC source, not the static menu subset",
        )


if __name__ == "__main__":
    unittest.main()
