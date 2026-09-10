"""Source-backed opening state maps cover every selectable base fighter."""

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
        }
        self.assertEqual(set(spec["fighters"]), set(expected))
        for name, (start, end) in expected.items():
            fighter = spec["fighters"][name]
            self.assertEqual(
                (fighter["action"]["start_frame"], fighter["action"]["end_frame"]),
                (start, end),
            )
            self.assertEqual(sorted(fighter["state_frames"].values()), [1, 2, 3])
            self.assertEqual(len(fighter["state_frames"]), 3)

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
