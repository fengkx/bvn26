"""Source-first regression for 李洛克's base timeline.

This test deliberately reads the locked SWF/script inputs at test time.  It
does not assert a guessed runtime shape or open the character in the shared
selection registry.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from inspect_swf import inspect  # noqa: E402


class LeeSourceAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.swf = ROOT / "game/fighter/lee.swf"
        self.bundle_path = ROOT / "scripts/fighter/lee.json"
        self.bundle = json.loads(self.bundle_path.read_text(encoding="utf-8"))
        self.scripts = {item["path"]: item["source"] for item in self.bundle["scripts"]}
        self.timeline = next(
            item for item in inspect(self.swf)["timelines"] if item["name"] == "sprite_518"
        )

    def test_locked_source_identity_and_base_timeline(self) -> None:
        self.assertEqual(
            hashlib.sha256(self.swf.read_bytes()).hexdigest(),
            "2443dc112dbf2be696abb9d924831814ae01990536df8298fa2c1432f35c93d1",
        )
        self.assertEqual(
            hashlib.sha256(self.bundle_path.read_bytes()).hexdigest(),
            "82230e0e97e0b2751ecba3e27b6f82e46c467ae956c51b0a2ba4d9c114c7e967",
        )
        self.assertEqual(self.timeline["declared_frames"], 1297)
        labels = {item["label"]: item["frame"] for item in self.timeline["labels"]}
        self.assertEqual(labels["站立"], 1)
        self.assertEqual(labels["砍1"], 157)
        self.assertEqual(labels["必杀"], 574)
        self.assertEqual(labels["超必杀"], 795)
        self.assertNotIn("万解", labels)

    def test_source_first_lifecycle_anchors(self) -> None:
        load = self.scripts[
            "frame_1/PlaceObject2_518_1/CLIPACTIONRECORD onClipEvent(load).as"
        ]
        self.assertIn("var spd = 10;", load)
        self.assertIn("var jumpPower = 15;", load)
        self.assertEqual(
            self.scripts["DefineSprite_518/frame_575/DoAction.as"],
            "bs = 1;\r\nql -= 100;\r\n",
        )
        self.assertEqual(
            self.scripts["DefineSprite_518/frame_796/DoAction.as"],
            "动作 = 3;\r\nbs = 1;\r\nql -= 300;\r\njump = 1;\r\njumped = 0;\r\n",
        )
        self.assertIn(
            'gotoAndStop("站立");',
            self.scripts["DefineSprite_518/frame_634/DoAction.as"],
        )
        self.assertIn(
            'gotoAndStop("必杀1");',
            self.scripts["DefineSprite_518/frame_625/DoAction.as"],
        )

    def test_all_timeline_scripts_are_retained_for_audit(self) -> None:
        scoped = [
            path for path in self.scripts
            if path.startswith("DefineSprite_518/")
        ]
        self.assertEqual(len(scoped), 167)
        self.assertIn("DefineSprite_518/frame_653/PlaceObject2_18_28/CLIPACTIONRECORD onClipEvent(enterFrame).as", scoped)
        self.assertIn("DefineSprite_518/frame_1075/PlaceObject2_18_30/CLIPACTIONRECORD onClipEvent(enterFrame).as", scoped)

    def test_generated_slice_keeps_source_identity_and_intro_states(self) -> None:
        slice_data = json.loads((ROOT / "data/slices/lee-base.json").read_text(encoding="utf-8"))
        timeline = json.loads((ROOT / "data/slices/lee-base.timeline.json").read_text(encoding="utf-8"))
        model = json.loads((ROOT / "data/actions/lee-base.json").read_text(encoding="utf-8"))
        intro = json.loads((ROOT / "godot/generated/fighters/lee/intro.json").read_text(encoding="utf-8"))
        self.assertEqual(slice_data["source"]["timeline_symbol_id"], 518)
        self.assertEqual(timeline["sprite_id"], 518)
        self.assertEqual(model["timeline_symbol_id"], 518)
        self.assertEqual(intro["source_sprite_id"], 518)
        self.assertEqual(intro["state_frames"], {"1159": 1, "1161": 3, "1219": 2})


if __name__ == "__main__":
    unittest.main()
