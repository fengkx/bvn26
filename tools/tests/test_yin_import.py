"""Gin reuses the audited controller and receiver without character overrides."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class YinImportTests(unittest.TestCase):
    def test_shared_controller_receiver_and_body_are_identical_to_renji(self):
        bundles = [read(f"scripts/fighter/{name}.json") for name in ("yin", "Renji")]
        scripts = [{s["path"]: s["source"] for s in b["scripts"]} for b in bundles]
        for path in ("DefineSprite_16/frame_1/DoAction.as", "DefineSprite_2/frame_1/DoAction.as"):
            self.assertEqual(scripts[0][path], scripts[1][path])
        self.assertEqual(scripts[0]["DefineSprite_435/frame_1/DoAction.as"],
                         scripts[1]["DefineSprite_717/frame_1/DoAction.as"])

    def test_source_super_and_receiver_frames(self):
        model = read("data/actions/yin-base.json")
        self.assertFalse(model["extracted_partial"])
        self.assertEqual(model, read("godot/generated/fighters/yin/combat.json"))
        self.assertEqual([(e["frame"], e["op"]) for e in model["super_events"]],
                         [(579, "super_start"), (602, "super_end"),
                          (652, "super_start"), (674, "super_end"),
                          (768, "super_start"), (800, "super_end")])
        self.assertEqual([(e["frame"], e["flying"]) for e in model["on_be_hit_frames"]],
                         [(988, False), (1001, True)])
        self.assertEqual(model["on_defence_frames"][0]["frame"], 976)
        self.assertEqual(model["action_exits"]["被打"]["frame"], 997)
        self.assertEqual(model["action_exits"]["起身"]["frame"], 1058)

    def test_rounded_motion_and_cancel_placement_survive_compilation(self):
        model = read("data/actions/yin-base.json")
        retreat = next(w for w in model["motion_windows"] if w["start_frame"] == 421)
        self.assertEqual((retreat["end_frame"], retreat["forward_speed_factor"],
                          retreat["round_forward"]), (425, -0.5, True))
        controller = read("godot/generated/fighters/yin/player_controller/controller.json")
        # The callback belongs to the new frame-202 placement, not frame 199's motion clip.
        cancel = next(h for h in controller["hooks"] if "/frame_202/" in h["path"])
        self.assertEqual(cancel["placement_frame"], 202)
        self.assertEqual(cancel["member_frames"][0], 202)
        generated = (ROOT / "godot/generated/fighters/yin/player_controller/controller.gd").read_text()
        self.assertIn('source_round((number(value("speed")) / number(2)))', generated)


if __name__ == "__main__":
    unittest.main()
