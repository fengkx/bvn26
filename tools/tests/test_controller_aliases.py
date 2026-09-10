"""Source-identical controller aliases keep their independent placements."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
from compile_ai_controller import compile_controller
from compile_ai_predicates import controller_script


class ControllerAliasTests(unittest.TestCase):
    def test_sasuke_controller_aliases_are_compiled_as_hooks(self):
        bundle = json.loads((ROOT / "scripts/fighter/Sasuke.json").read_text())
        timeline = json.loads((ROOT / "data/slices/Sasuke-base.timeline.json").read_text())
        self.assertEqual(controller_script(bundle, 603)["path"], "DefineSprite_16/frame_1/DoAction.as")
        _, metadata = compile_controller(bundle, 603, timeline)
        controller_hooks = [hook for hook in metadata["hooks"] if "controller_id" in hook]
        self.assertEqual({hook["controller_id"] for hook in controller_hooks}, {16, 488})
        self.assertTrue(any("frame_927/PlaceObject2_488_28" in hook["path"] for hook in controller_hooks))
        self.assertFalse(any("frame_927/PlaceObject2_488_28" in hook["path"]
                             for hook in metadata["projectile_hooks"]))


if __name__ == "__main__":
    unittest.main()
