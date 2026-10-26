"""Check the imported map labels and assets against the locked catalog."""

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StageCatalogTests(unittest.TestCase):
    def test_shared_world_cannot_drop_authored_obligation_frame(self):
        from tools.importer.placement_build_guard import validate_build_placements
        path = ROOT / "godot/generated/stages/catalog/world/timeline.json"
        timeline = json.loads(path.read_text())
        validate_build_placements(timeline, str(path))
        timeline["frames"] = [frame for frame in timeline["frames"] if frame["frame"] != 6]
        with self.assertRaisesRegex(ValueError,
                r"missing source timeline frame: game/main.swf sprite 1738 frame 6 depth 17"):
            validate_build_placements(timeline, str(path))

    def test_all_source_maps_have_spawn_markers_and_intact_assets(self):
        directory = ROOT / "godot/generated/stages/catalog"
        catalog = json.loads((directory / "catalog.json").read_text())
        source = json.loads((ROOT / "manifest.json").read_text())["map_catalog"]
        self.assertEqual({stage["id"] for stage in catalog["stages"]}, set(source))
        self.assertEqual({stage["directory"] for stage in catalog["stages"]}, {"world"})
        legacy = json.loads((ROOT / "godot/generated/stages/current_world/timeline.json").read_text())
        self.assertEqual([f["frame"] for f in legacy["frames"]], list(range(1, legacy["frame_count"] + 1)))
        for stage in catalog["stages"]:
            with self.subTest(stage=stage["id"]):
                folder = directory / stage["directory"]
                timeline = json.loads((folder / "timeline.json").read_text())
                self.assertNotIn("wrapper", timeline)
                background = json.loads((directory / stage["background_directory"] / "timeline.json").read_text())
                self.assertEqual(background["sprite_id"], 1501)
                self.assertIn(source[stage["id"]]["frame"], background["frames"][0]["labels"])
                for definition in timeline["definitions"]:
                    if definition["character_id"] == 1690:
                        self.assertFalse(definition["initial_visible"])
                self.assertEqual([f["frame"] for f in timeline["frames"]],
                                 list(range(1, timeline["frame_count"] + 1)))
                frame = next(f for f in timeline["frames"] if f["frame"] == stage["frame"])
                self.assertIn(source[stage["id"]]["frame"], frame["labels"])
                names = {item.get("name") for item in frame["display_list"]}
                for item in frame["display_list"]:
                    if item.get("name") in {"p1", "p2", "p1fz", "p2fz"}:
                        self.assertTrue(item["replaced_by_external_movie"])
                self.assertTrue({"p1", "p2"} <= names)
                assets = json.loads((folder / "assets.json").read_text())["assets"]
                for asset in assets:
                    self.assertEqual(
                        hashlib.sha256(
                            (folder / asset["path"]).read_bytes()
                        ).hexdigest(),
                        asset["sha256"],
                    )


if __name__ == "__main__":
    unittest.main()
