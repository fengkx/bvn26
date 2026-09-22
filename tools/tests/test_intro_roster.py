"""Source-backed opening state maps cover selectable and staged base forms."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class IntroRosterTests(unittest.TestCase):
    def test_each_selectable_base_fighter_has_own_source_opening_chain(self):
        spec = json.loads((ROOT / "godot/generated/main/intro/intro.json").read_text())
        expected = {
            "minren": (1099, 1178),
            "yihu": (822, 901),
            "rifagu": (983, 1062),
            "sasuke": (946, 1025),
            "kakashi": (1201, 1280),
            "renji": (1053, 1132),
            "sakura": (975, 1054),
            "rukia": (1003, 1082),
            "yulong": (1133, 1212),
            "byakuya": (958, 1034),
            "lee": (1158, 1237),
        }
        self.assertEqual(set(spec["fighters"]), set(expected))
        for name, (start, end) in expected.items():
            fighter = spec["fighters"][name]
            self.assertEqual(
                (fighter["action"]["start_frame"], fighter["action"]["end_frame"]),
                (start, end),
            )
            self.assertEqual(set(fighter["state_frames"].values()), {1, 2, 3})
            self.assertGreaterEqual(len(fighter["state_frames"]), 3)

    def test_published_candidate_roster_has_source_openings(self):
        available = json.loads(
            (ROOT / "godot/generated/main/character_selection/available.json").read_text()
        )
        intro = json.loads((ROOT / "godot/generated/main/intro/intro.json").read_text())
        for name in ("sakura", "rukia", "yulong", "byakuya", "lee"):
            self.assertIn(name, intro["fighters"])
            self.assertIn(name, available["fighters"].values())
        self.assertIn("jinye", available["helpers"].values())

    def test_source_audit_and_runtime_intro_have_same_roster(self):
        audit = json.loads((ROOT / "evidence/intro-source.json").read_text())
        runtime = json.loads((ROOT / "godot/generated/main/intro/intro.json").read_text())
        self.assertEqual(set(audit["fighters"]), set(runtime["fighters"]))
        for name in runtime["fighters"]:
            self.assertEqual(
                audit["fighters"][name]["state_frames"],
                runtime["fighters"][name]["state_frames"],
            )


if __name__ == "__main__":
    unittest.main()
