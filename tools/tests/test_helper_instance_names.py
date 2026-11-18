"""Check that helper hit regions follow authored instance names."""

import json
from pathlib import Path
import tempfile
import unittest

from tools.importer.build_helper_model import build_model


class HelperInstanceNameTests(unittest.TestCase):
    swf = Path("game/fighter/fz/zuojin.swf")
    scripts = Path("scripts/fighter/fz/zuojin.json")

    def test_sai_renames_the_same_placed_sprite(self):
        model = build_model(self.scripts, self.swf, "佐井")
        events = model["instance_names"]["27"]
        self.assertEqual([(e["frame"], e["name"]) for e in events], [(5, "atm1"), (8, "abcd")])
        published = json.loads(Path("godot/generated/helpers/zuojin/combat.json").read_text())
        self.assertEqual(published, model)

    def test_conditional_rename_requires_a_compiler_rule(self):
        bundle = json.loads(self.scripts.read_text())
        script = next(s for s in bundle["scripts"] if s["path"] == "DefineSprite_27/frame_5/DoAction.as")
        script["source"] = 'if (enabled) { _name = "atm1"; }'
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / "scripts.json"
            path.write_text(json.dumps(bundle))
            with self.assertRaisesRegex(ValueError, "Unsupported helper instance rename"):
                build_model(path, self.swf, "佐井")
