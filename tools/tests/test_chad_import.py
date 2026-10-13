"""Chad reuses the audited controller and receiver without character overrides."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads((ROOT / path).read_text())


class ChadImportTests(unittest.TestCase):
    def test_shared_controller_receiver_and_body_are_identical_to_renji(self):
        bundles = [read(f"scripts/fighter/{name}.json") for name in ("chad", "Renji")]
        scripts = [{s["path"]: s["source"] for s in b["scripts"]} for b in bundles]
        for path in ("DefineSprite_16/frame_1/DoAction.as", "DefineSprite_2/frame_1/DoAction.as"):
            self.assertEqual(scripts[0][path], scripts[1][path])
        self.assertEqual(scripts[0]["DefineSprite_607/frame_1/DoAction.as"],
                         scripts[1]["DefineSprite_717/frame_1/DoAction.as"])

    def test_source_super_and_receiver_frames(self):
        model = read("data/actions/chad-base.json")
        self.assertFalse(model["extracted_partial"])
        self.assertEqual(model, read("godot/generated/fighters/chad/combat.json"))
        self.assertEqual([(e["frame"], e["op"]) for e in model["super_events"]],
                         [(482, "super_start"), (495, "super_end"),
                          (550, "super_start"), (566, "super_end"),
                          (646, "super_start"), (662, "super_end")])
        self.assertEqual([(e["frame"], e["flying"]) for e in model["on_be_hit_frames"]],
                         [(814, False), (827, True)])
        self.assertEqual(model["on_defence_frames"][0]["frame"], 802)
        self.assertEqual(model["action_exits"]["被打"]["frame"], 823)
        self.assertEqual(model["action_exits"]["起身"]["frame"], 885)

    def test_contact_branches_and_cancel_lifetimes_survive_compilation(self):
        controller = read("godot/generated/fighters/chad/player_controller/controller.json")
        for start, end in [(190, 194), (208, 215), (245, 252), (394, 401), (662, 671)]:
            hook = next(h for h in controller["hooks"] if h["placement_frame"] == start)
            self.assertEqual(hook["member_frames"], list(range(start, end + 1)))
        generated = (ROOT / "godot/generated/fighters/chad/player_controller/controller.gd").read_text()
        for hitbox, label, factor in [("kj10atm", "砍技11", 3), ("zh20atm", "超必杀1", 4)]:
            self.assertIn(f'body_hit("{hitbox}")', generated)
            self.assertIn(f'adapter.goto_label("{label}", true)', generated)
            self.assertIn(f'moveX((number(value("speed")) * number({factor})))', generated)
        self.assertIn('moveX(8)', generated)
        self.assertIn('moveY(15)', generated)
        model = read("data/actions/chad-base.json")
        self.assertIn({"from": "超必杀1", "to": "超必杀0", "frame": 698,
                       "condition": "timeline_fallthrough"}, model["timeline_fallthroughs"])


if __name__ == "__main__":
    unittest.main()
