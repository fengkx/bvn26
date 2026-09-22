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
    def test_byakuya_base_controller_uses_frame_one_alias(self):
        bundle = json.loads((ROOT / "scripts/fighter/Byakuya.json").read_text())
        self.assertEqual(controller_script(bundle, 631)["path"], "DefineSprite_16/frame_1/DoAction.as")

    def test_byakuya_child_controller_callbacks_are_compiled(self):
        bundle = json.loads((ROOT / "scripts/fighter/Byakuya.json").read_text())
        timeline = json.loads((ROOT / "data/slices/Byakuya-base.timeline.json").read_text())
        native, metadata = compile_controller(bundle, 631, timeline)
        child = [hook for hook in metadata["hooks"] if hook.get("child_controller")]
        paths = {hook["path"] for hook in child}
        for frame in (134, 139, 229, 293):
            self.assertIn(
                f"DefineSprite_631/frame_{frame}/PlaceObject2_69_34/CLIPACTIONRECORD onClipEvent(enterFrame).as",
                paths,
            )
        self.assertIn("DefineSprite_631/frame_852/PlaceObject2_572_28/CLIPACTIONRECORD onClipEvent(enterFrame).as", paths)
        self.assertIn('adapter.effect("bdfyxg")', native)
        self.assertIn("func child_69_magichit1", native)
        self.assertIn("child_69_bisha()", native)

    def test_byakuya_nested_controller_uses_its_source_abi(self):
        bundle = json.loads((ROOT / "scripts/fighter/Byakuya.json").read_text())
        scripts = {item["path"]: item["source"] for item in bundle["scripts"]}
        nested = scripts["DefineSprite_69/frame_1/DoAction.as"]
        self.assertRegex(nested, r"function magichit1\(\)")
        self.assertRegex(nested, r"function bisha\(\)")
        self.assertRegex(nested, r"function jumpDown\(\)")
        self.assertIn("jiao.hitTest", nested)
        self.assertIn("_parent.jiao.hitTest", nested)
        self.assertIn("_parent._parent._y + 20", nested)

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
