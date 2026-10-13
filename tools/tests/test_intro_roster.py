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
            "yin": (1072, 1151),
            "neji": (1191, 1298),
