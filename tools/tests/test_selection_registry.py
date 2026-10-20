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
    def test_published_roster_matches_complete_base_artifacts(self):
        first = build_available(ROOT)
        second = build_available(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(
            set(first["fighters"]),
            {"鸣人", "一护", "日番谷", "佐助", "卡卡西", "恋次", "樱", "露其雅", "石田", "白哉", "小李", "银", "茶渡", "宁次", "一角", "鼬", "大蛇丸", "自来也", "佩恩", "小南", "带土", "迪达拉"},
        )
        self.assertEqual(set(first["helpers"]), {"我爱罗", "魂", "鼬", "松本"})

        published = json.loads(
            (ROOT / "godot/generated/main/character_selection/available.json").read_text()
        )
        self.assertEqual(published, first)

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
        selection = json.loads((directory / "selection.json").read_text())
        portraits = json.loads((directory / "portraits.json").read_text())
        footer = json.loads((directory / "footer.json").read_text())
        fighter_cards = {card["id"]: card for card in selection["phases"][0]["cards"]}
        self.assertEqual(
            set(portraits),
            {"鸣人", "一护", "日番谷", "佐助", "卡卡西", "恋次", "樱", "露其雅", "石田", "白哉", "小李", "银", "茶渡", "宁次", "一角", "鼬", "大蛇丸", "自来也", "佩恩", "小南", "带土", "迪达拉"},
        )
        self.assertEqual(
            set(footer),
            {
                "鸣人", "一护", "日番谷", "佐助", "卡卡西", "恋次",
                "樱", "露其雅", "石田", "白哉", "小李", "银", "茶渡", "宁次", "一角", "魂", "我爱罗", "鼬", "松本", "大蛇丸", "自来也", "佩恩", "小南", "带土", "迪达拉",
            },
        )
        for entry in portraits.values():
            for texture in entry["textures"]:
                self.assertTrue((directory / texture).is_file(), texture)
        for entry in footer.values():
            self.assertTrue((directory / entry["texture"]).is_file(), entry["texture"])
        for name in ("白哉", "小李", "银", "茶渡", "宁次", "一角", "鼬", "大蛇丸", "自来也", "佩恩", "小南", "带土", "迪达拉"):
            card = fighter_cards[name]
            # This frame belongs to the card's namemc clip; the baked portrait
            # is selected by its independent Sprite_1346 source label frame.
            self.assertGreater(card["portrait_frame"], 0)
            self.assertEqual(len(portraits[name]["textures"]), 5)
            self.assertEqual(footer[name]["text"], card["display_name"])
            self.assertTrue(all((directory / path).is_file() for path in portraits[name]["textures"]))
        self.assertEqual({name: portraits[name]["source_label_frame"] for name in ("白哉", "小李")},
            {"白哉": 9, "小李": 28})


if __name__ == "__main__":
    unittest.main()
