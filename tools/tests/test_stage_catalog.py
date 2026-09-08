"""Check the imported map labels and assets against the locked catalog."""

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StageCatalogTests(unittest.TestCase):
    def test_all_source_maps_have_spawn_markers_and_intact_assets(self):
        directory = ROOT / "godot/generated/stages/catalog"
        catalog = json.loads((directory / "catalog.json").read_text())
        source = json.loads((ROOT / "manifest.json").read_text())["map_catalog"]
        self.assertEqual({stage["id"] for stage in catalog["stages"]}, set(source))
        for stage in catalog["stages"]:
            with self.subTest(stage=stage["id"]):
                folder = directory / stage["directory"]
                timeline = json.loads((folder / "timeline.json").read_text())
                (frame,) = timeline["frames"]
                self.assertIn(source[stage["id"]]["frame"], frame["labels"])
                names = {item.get("name") for item in frame["display_list"]}
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
