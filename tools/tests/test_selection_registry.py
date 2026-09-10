"""Contract checks for the source-derived selectable artifact registry."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
from build_character_selection import build_available  # noqa: E402


class SelectionRegistryTests(unittest.TestCase):
    def test_registry_is_deterministic_and_only_contains_base_forms(self):
        first = build_available(ROOT)
        second = build_available(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(
            set(first["fighters"]), {"鸣人", "一护", "日番谷", "佐助", "卡卡西", "恋次"}
        )
        self.assertEqual(set(first["helpers"]), {"我爱罗", "魂", "鼬"})
        self.assertNotIn("佐助咒怨", first["fighters"])
        self.assertNotIn("佐助须佐", first["fighters"])
        self.assertNotIn("鸣人九尾", first["fighters"])
        self.assertNotIn("一护万解", first["fighters"])
        manifest = json.loads((ROOT / "manifest.json").read_text())[
            "fighter_catalog"
        ]
        for name, slug in first["fighters"].items():
            self.assertNotIn("WKframe", manifest[name])
            model = json.loads(
                (ROOT / "godot/generated/fighters" / slug / "fighter.json").read_text()
            )
            self.assertEqual(model["fighter_id"], name)
            self.assertEqual(model["form_frame"], 1)

    def test_helper_registry_matches_compiled_helper_identity(self):
        for name, slug in build_available(ROOT)["helpers"].items():
            model = json.loads(
                (ROOT / "godot/generated/helpers" / slug / "combat.json").read_text()
            )
            self.assertEqual(model["helper_id"], name)

    def test_new_roster_entries_have_source_baked_portrait_and_footer_names(self):
        directory = ROOT / "godot/generated/main/character_selection"
        portraits = json.loads((directory / "portraits.json").read_text())
        footer = json.loads((directory / "footer.json").read_text())
        self.assertEqual(
            set(portraits), {"鸣人", "一护", "日番谷", "佐助", "卡卡西", "恋次"}
        )
        self.assertEqual(
            set(footer), {"鸣人", "一护", "日番谷", "佐助", "卡卡西", "恋次", "魂", "我爱罗", "鼬"}
        )
        for entry in portraits.values():
            for texture in entry["textures"]:
                self.assertTrue((directory / texture).is_file(), texture)
        for entry in footer.values():
            self.assertTrue((directory / entry["texture"]).is_file(), entry["texture"])


if __name__ == "__main__":
    unittest.main()
