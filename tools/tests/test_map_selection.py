"""Source and captured-oracle checks for the map-selection compiler output."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class MapSelectionTests(unittest.TestCase):
    def test_menu_grid_matches_locked_map_catalog(self):
        output = ROOT / "godot/generated/main/map_selection"
        spec = json.loads((output / "presentation.json").read_text())
        manifest = json.loads((ROOT / "manifest.json").read_text())
        self.assertEqual(
            {card["id"] for card in spec["cards"]}, set(manifest["map_catalog"])
        )
        self.assertEqual(
            {tuple(card["grid"]) for card in spec["cards"]},
            {(x, y) for x in (1, 8) for y in (0, 2, 4, 6, 8)},
        )
        for index, card in enumerate(spec["cards"]):
            self.assertTrue((output / card["texture"]).is_file())
            self.assertTrue((output / f"name_{index}.png").is_file())
        self.assertEqual(spec["repeat_frames"], 5)
        self.assertEqual(spec["confirm_delay_ms"], 500)
        self.assertEqual((spec["entry_frame"], spec["stop_frame"]), (35, 50))

    def test_native_player_input_capture(self):
        capture = (ROOT / "evidence/content/map-selection/input.log").read_text()
        self.assertIn("tick=1 stage=流魂街 repeat=0 enabled=true", capture)
        self.assertIn("tick=5 stage=流魂街 repeat=4 enabled=true", capture)
        self.assertIn("tick=6 stage=双极 repeat=0 enabled=true", capture)
        self.assertIn("tick=12 stage=双极 repeat=0 enabled=false", capture)
        self.assertIn("MAP_CONFIRM elapsed_ms=", capture)


if __name__ == "__main__":
    unittest.main()
