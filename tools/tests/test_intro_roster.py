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
            "orochimaru": (1186, 1293),
            "jiraiya": (1118, 1220),
            "pain": (1266, 1326),
            "konan": (1161, 1240),
            "daitu": (1148, 1208),
            "didala": (988, 1088),
            "lanran": (1617, 1693),
            "gaara": (1176, 1283),
            "juggo": (1226, 1313),
            "qilabi": (1131, 1203),
            "jianba": (1132, 1188),
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
            "yin": (1072, 1151),
            "chad": (898, 974),
            "neji": (1191, 1298),
            "yijiao": (917, 981),
            "itachi": (1094, 1173),
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
        for name in ("sakura", "rukia", "yulong", "byakuya", "lee", "yin", "chad", "yijiao"):
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
