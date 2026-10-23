"""Sasuke source rules that must survive combat and AI compilation."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
from build_combat_model import parse_body_warp
from compile_ai_context import compile_context


class SasukeCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / "scripts/fighter/Sasuke.json").read_text())
        cls.timeline = json.loads((ROOT / "data/slices/sasuke-base.timeline.json").read_text())

    def test_facing_only_body_warp_preserves_both_source_offsets(self):
        source = next(
            item["source"]
            for item in self.bundle["scripts"]
            if item["path"] == "DefineSprite_603/frame_408/DoAction.as"
        )
        self.assertEqual(parse_body_warp(source), {
            "op": "warp_to_opponent",
            "place_x": True,
            "xscale_gt_0": {"x_pixels": -20.0},
            "xscale_lt_0": {"x_pixels": 20.0},
        })

    def test_frame_calls_keep_source_fifo_and_line_for_frame_408_warp(self):
        with self.assertRaisesRegex(ValueError, r'Sasuke.swf.*frame_1232.*uncompiled frame call'):
            compile_context(self.bundle, self.timeline)
        # Only the source FIFO at 408 is under test; the full slice must fail.
        timeline = {**self.timeline, 'frames': [f for f in self.timeline['frames'] if f['frame'] in (1, 408)]}
        context = compile_context(self.bundle, timeline)
        calls = context["frame_calls"]["408"]
        warp = next(call for call in calls if call["op"] == "body_warp")
        self.assertEqual(warp["frame"], 408)
        self.assertEqual(warp["path"], "DefineSprite_603/frame_408/DoAction.as")
        self.assertEqual(warp["line"], 1)
        self.assertEqual(warp["warp"]["xscale_gt_0"], {"x_pixels": -20.0})
        self.assertEqual(warp["warp"]["xscale_lt_0"], {"x_pixels": 20.0})


if __name__ == "__main__":
    unittest.main()
