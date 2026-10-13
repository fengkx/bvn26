"""Lock Neji's source placements, warps and shared interrupt/guard implementation."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class NejiImportTests(unittest.TestCase):
    def test_controller_receiver_and_body_match_audited_renji(self):
        bundles = [read(f"scripts/fighter/{name}.json") for name in ("neji", "Renji")]
        scripts = [{s["path"]: s["source"] for s in b["scripts"]} for b in bundles]
        for first, second in ((20, 16), (2, 2), (535, 717)):
            self.assertEqual(scripts[0][f"DefineSprite_{first}/frame_1/DoAction.as"],
                             scripts[1][f"DefineSprite_{second}/frame_1/DoAction.as"])

    def test_moving_hitbox_and_opponent_relative_teleport(self):
        model = read("data/actions/neji-base.json")
        self.assertFalse(model["extracted_partial"])
        self.assertEqual(model, read("godot/generated/fighters/neji/combat.json"))
        projectile, = model["projectiles"]
        self.assertEqual((projectile["instance_name"], projectile["start_frame"],
                          projectile["end_frame"], projectile["local_x_delta"]),
                         ("zh1atm", 391, 404, 20))
        self.assertEqual(projectile["collision_queries"], [])
        warp, = model["body_warps"]
        self.assertEqual(warp["frame"], 478)
        self.assertEqual(warp["xscale_gt_0"], {"x_pixels": -30})
        self.assertEqual(warp["xscale_lt_0"], {"x_pixels": 30})
        self.assertTrue(warp["place_y"])

    def test_super_pause_and_receiver_frames(self):
        model = read("data/actions/neji-base.json")
        self.assertEqual([(e["frame"], e["op"]) for e in model["super_events"]],
                         [(508, "super_start"), (521, "super_end"),
                          (588, "super_start"), (601, "super_end"),
                          (652, "super_start"), (689, "super_end")])
        self.assertEqual([(e["frame"], e["flying"]) for e in model["on_be_hit_frames"]],
                         [(1108, False), (1121, True)])
        self.assertEqual(model["on_defence_frames"][0]["frame"], 1096)
        controller = read("godot/generated/fighters/neji/player_controller/controller.json")
        cancel = next(h for h in controller["hooks"] if "/frame_224/" in h["path"])
        self.assertEqual(cancel["placement_frame"], 224)
        self.assertEqual(cancel["member_frames"][0], 224)


if __name__ == "__main__":
    unittest.main()
