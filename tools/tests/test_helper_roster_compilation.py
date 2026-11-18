"""Rebuild the new helper roster from its original inputs."""

import json
from pathlib import Path
import unittest

from tools.importer.build_helper_model import build_model


ROOT = Path(__file__).resolve().parents[2]


class HelperRosterCompilationTests(unittest.TestCase):
    def test_catalog_models_reproduce_from_original_inputs(self):
        catalog = json.loads((ROOT / "manifest.json").read_text())["fighter_catalog"]
        fixtures = ROOT / "evidence/helpers/remaining-roster"
        for name, entry in catalog.items():
            if "fzurl" not in entry:
                continue
            slug = Path(entry["fzurl"]).stem
            if not (fixtures / slug / "summon.json").is_file():
                continue
            with self.subTest(helper=slug):
                model_path = ROOT / f"data/actions/{slug}-helper.json"
                model = json.loads(model_path.read_text())
                source = model["source"]
                rebuilt = build_model(
                    Path(source["script_bundle"]), Path(source["swf"]), name,
                    ROOT / f"data/slices/{slug}-helper.timeline.json",
                )
                self.assertEqual(rebuilt, model)
                runtime = ROOT / "godot/generated/helpers" / slug / "combat.json"
                self.assertEqual(model_path.read_bytes(), runtime.read_bytes())
