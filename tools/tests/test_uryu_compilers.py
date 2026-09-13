"""Uryu compiler fixtures retain source scope and child load state."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
from compile_ai_context import compile_context
from compile_ai_controller import compile_controller, source_expression
from build_combat_model import parse_projectile_initialization, parse_projectile_motion


class UryuCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / "scripts/fighter/yulong.json").read_text())
        cls.timeline = json.loads((ROOT / "data/slices/yulong-base.timeline.json").read_text())

    def test_place_object3_form_load_and_parent_counter_lifecycle(self):
        context = compile_context(self.bundle, self.timeline)

        self.assertIn(
            "frame_1/PlaceObject3_345_1/CLIPACTIONRECORD onClipEvent(load).as",
            {item["path"] for item in self.bundle["scripts"]},
        )
        self.assertEqual(context["controller_scope_fields"], ["k1n"])
        self.assertEqual(
            next(event for event in context["frame_writes"]["1"] if event["field"] == "k1n"),
            {
                "field": "k1n", "value": 0,
                "path": "DefineSprite_345/frame_1/DoAction.as", "line": 942,
            },
        )
        self.assertEqual(
            next(event for event in context["frame_writes"]["184"] if event.get("field") == "k1n" or event.get("op") == "increment"),
            {
                "op": "increment", "field": "k1n", "delta": 1,
                "path": "DefineSprite_345/frame_184/DoAction.as", "line": 2,
            },
        )

    def test_controller_compiles_only_declared_parent_scope_and_literal_projectile_state(self):
        code, metadata = compile_controller(
            self.bundle, self.timeline["sprite_id"], self.timeline, player=True
        )

        self.assertIn('value("k1n")', code)
        self.assertEqual(metadata["controller_scope_fields"], ["k1n"])
        projectile = next(
            hook["projectile"] for hook in metadata["projectile_hooks"]
            if hook["placement_frame"] == 188
        )
        self.assertEqual(projectile["initial_variables"], {"played": 0, "movspeed": 20})
        self.assertEqual(projectile["local_x_factor"], 1.0)
        self.assertEqual(projectile["on_hit_goto_frame"], 5)
        self.assertTrue(projectile["on_hit_goto_grouped"])

    def test_unknown_parent_field_remains_an_error(self):
        with self.assertRaisesRegex(ValueError, "Unsupported AI expression"):
            source_expression("_parent.unbound < 3", set(), {"k1n"})

    def test_literal_load_state_rejects_non_literal_or_duplicate_writes(self):
        self.assertEqual(
            parse_projectile_initialization("onClipEvent(load){var played = 0;\nvar movspeed = 20;}"),
            {"initial_variables": {"played": 0, "movspeed": 20}},
        )
        self.assertEqual(
            parse_projectile_initialization("onClipEvent(load){movspeed = _parent.speed;}"),
            {"initial_speed_field": "speed", "initial_speed_factor": 1.0},
        )
        with self.assertRaisesRegex(ValueError, "Duplicate projectile local declaration"):
            parse_projectile_initialization("onClipEvent(load){var played = 0;\nvar played = 1;}")

    def test_projectile_hit_local_writes_keep_one_shot_guard_as_a_group(self):
        script = next(
            item["source"] for item in self.bundle["scripts"]
            if item["path"].endswith("frame_188/PlaceObject2_104_28/CLIPACTIONRECORD onClipEvent(enterFrame).as")
        )
        motion = parse_projectile_motion(script)
        self.assertEqual(motion["on_hit_events"], [{
            "op": "local_write_group",
            "conditions": [{"field": "played", "operator": "==", "value": 0}],
            "source_scope": [398],
            "writes": [{"field": "played", "value": 1}, {"field": "movspeed", "value": 0}],
            "goto_frame": 5,
        }])
        self.assertTrue(motion["on_hit_goto_grouped"])

    def test_air_attack_literal_motion_keeps_local_pixel_deltas(self):
        script = next(
            item["source"] for item in self.bundle["scripts"]
            if item["path"].endswith(
                "frame_137/PlaceObject2_74_28/CLIPACTIONRECORD onClipEvent(enterFrame).as"
            )
        )
        motion = parse_projectile_motion(script)
        self.assertEqual(motion["local_x_delta"], 20.0)
        self.assertEqual(motion["local_y_delta"], 10.0)
        self.assertNotIn("local_x_factor", motion)
        self.assertNotIn("local_y_factor", motion)
        self.assertEqual(motion["on_hit_goto_frame"], 5)
        self.assertEqual(motion["on_hit_events"][0]["goto_frame"], 5)
        self.assertTrue(motion["on_hit_goto_grouped"])
        self.assertEqual(
            motion["local_motion_conditions"],
            [{"field": "played", "operator": "==", "value": 0}],
        )

    def test_independent_equal_guards_do_not_merge_into_one_source_block(self):
        motion = parse_projectile_motion("""\
if (mian.hitTest(_root.game[\"p\" + _parent.pn].mc.bdmn)) {
    _X = _X + movspeed;
    if (played == 0) { played = 1; }
    if (played == 0) { gotoAndPlay(5); }
}
""")
        self.assertEqual(len(motion["on_hit_events"]), 1)
        self.assertEqual(motion["on_hit_events"][0]["writes"], [{"field": "played", "value": 1}])
        self.assertNotIn("goto_frame", motion["on_hit_events"][0])
        self.assertFalse(motion.get("on_hit_goto_grouped", False))

    def test_unrecognized_nested_projectile_guard_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Uncompiled projectile local guard"):
            parse_projectile_motion("""\
if (mian.hitTest(_root.game[\"p\" + _parent.pn].mc.bdmn)) {
    _X = _X + movspeed;
    if (_parent.unknown == 0) {
        if (played == 0) { played = 1; gotoAndPlay(5); }
    }
}
""")

    def test_unsupported_local_write_and_goto_block_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "local-write/goto guard lacks"):
            parse_projectile_motion("""\
if (mian.hitTest(_root.game[\"p\" + _parent.pn].mc.bdmn)) {
    if (movspeed == 0) { movspeed = 1; gotoAndPlay(5); }
    _X = _X + movspeed;
}
""")

    def test_projectile_literal_motion_rejects_ambiguous_axis_updates(self):
        with self.assertRaisesRegex(ValueError, "multiple literal deltas"):
            parse_projectile_motion("_X = _X + 20; _X = _X - 5;")
        with self.assertRaisesRegex(ValueError, "mixes literal and movspeed"):
            parse_projectile_motion("_X = _X + movspeed; _X = _X + 20;")

    def test_unrecognized_projectile_load_side_effect_fails_closed(self):
        bundle = json.loads(json.dumps(self.bundle))
        load = next(
            item for item in bundle["scripts"]
            if item["path"] == (
                "DefineSprite_345/frame_188/PlaceObject2_104_28/"
                "CLIPACTIONRECORD onClipEvent(load).as"
            )
        )
        load["source"] = "onClipEvent(load){playSound(\"launch\");}"

        with self.assertRaisesRegex(ValueError, "Uncompiled projectile load statement"):
            compile_controller(bundle, self.timeline["sprite_id"], self.timeline, player=True)


if __name__ == "__main__":
    unittest.main()
