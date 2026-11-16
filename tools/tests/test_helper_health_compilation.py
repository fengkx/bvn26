"""Source-only compilation checks; these do not certify runtime healing."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.importer.build_helper_model import build_model

ROOT = Path(__file__).resolve().parents[2]


class HelperHealthCompilationTests(unittest.TestCase):
    def test_orihime_compiles_seven_separate_owner_additions(self):
        bundle_path = ROOT / "scripts/fighter/fz/zhiji.json"
        bundle = json.loads(bundle_path.read_text())
        swf = ROOT / "game/fighter/fz/zhiji.swf"
        self.assertEqual(hashlib.sha256(swf.read_bytes()).hexdigest(), bundle["swf_sha256"])
        model = build_model(bundle_path, swf, "织姬")
        events = model["health_events"]
        self.assertEqual([(e["frame"], e["delta"]) for e in events],
                         [(frame, 20) for frame in (41, 46, 50, 56, 61, 67, 75)])
        scripts = {s["path"]: s["source"] for s in bundle["scripts"]}
        for event in events:
            self.assertEqual(event["target"], "owner")
            self.assertEqual(event["op"], "add")
            source = scripts[event["source_path"]]
            self.assertEqual(source.strip(), '_root.game["p" + sn].mc.hp += 20;')
            self.assertEqual(event["source_sha256"], hashlib.sha256(source.encode()).hexdigest())
        self.assertEqual(model["end_frame"], 91)
        self.assertEqual(model["hide_frames"], [])

    def test_other_helpers_do_not_gain_health_events(self):
        for helper in ("you", "kon", "woailuo", "jinye", "jianba"):
            with self.subTest(helper=helper):
                model = build_model(ROOT / f"scripts/fighter/fz/{helper}.json",
                                    Path(f"game/fighter/fz/{helper}.swf"), helper,
                                    Path(f"data/slices/{helper}-helper.timeline.json"))
                self.assertNotIn("health_events", model)

    def test_rejects_conditions_other_targets_and_nested_callbacks(self):
        original = json.loads((ROOT / "scripts/fighter/fz/zhiji.json").read_text())
        cases = [
            ("frame_41/DoAction.as", 'if (ready) { _root.game["p" + sn].mc.hp += 20; }'),
            ("frame_41/DoAction.as", '_root.game["p" + pn].mc.hp += 20;'),
            ("frame_41/DoAction.as", '_root.game["p" + sn].mc.hp = 1000;'),
            ("frame_41/DoAction.as", '_root.game["p" + sn].mc.hp += 20; stop();'),
            ("DefineSprite_1/frame_41/DoAction.as", '_root.game["p" + sn].mc.hp += 20;'),
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "scripts.json"
            for script_path, source in cases:
                with self.subTest(source=source, path=script_path):
                    bundle = dict(original, scripts=[{"path": script_path, "source": source}])
                    path.write_text(json.dumps(bundle))
                    with self.assertRaisesRegex(ValueError, "Unsupported helper health write"):
                        build_model(path, ROOT / "game/fighter/fz/zhiji.swf", "织姬")


if __name__ == "__main__":
    unittest.main()
