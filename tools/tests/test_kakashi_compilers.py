"""Kakashi compiler fixtures lock source semantics without role-specific runtime code."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
from compile_ai_context import compile_context, _root_clip_rename_event
from compile_ai_controller import compile_controller
from build_combat_model import parse_clip_timeline, source_frame_counts
from build_combat_model import parse_projectile_motion


class KakashiCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((ROOT / "scripts/fighter/Kakashi.json").read_text())
        cls.timeline = json.loads((ROOT / "data/slices/Kakashi-base.timeline.json").read_text())

    def test_decimal_projectile_load_preserves_source_factor_and_scope(self):
        _, metadata = compile_controller(self.bundle, 710, self.timeline, player=True)
        hook = next(item for item in metadata["projectile_hooks"] if item["placement_frame"] == 162)
        projectile = hook["projectile"]
        self.assertEqual(projectile["initial_speed_field"], "speed")
        self.assertEqual(projectile["initial_speed_factor"], 2.5)
        self.assertNotIn("initial_played", projectile)
        self.assertEqual(projectile["local_x_factor"], 1.0)
        self.assertEqual(projectile["local_y_factor"], 1.0)

    def test_projectile_playheads_use_source_one_and_multi_frame_counts(self):
        _, metadata = compile_controller(self.bundle, 710, self.timeline)
        hooks = {item["placement_frame"]: item["projectile"]
                 for item in metadata["projectile_hooks"]}
        self.assertEqual(hooks[162]["frame_count"], 1)
        self.assertEqual(hooks[425]["frame_count"], 9)

    def test_missing_source_frame_count_fails_closed(self):
        timeline = json.loads(json.dumps(self.timeline))
        definition = next(item for item in timeline["definitions"]
                          if item["character_id"] == 74)
        del definition["frame_count"]
        counts = source_frame_counts(timeline)
        with self.assertRaisesRegex(ValueError, "Missing source frame_count"):
            parse_clip_timeline(self.bundle, 74, counts)
        with self.assertRaisesRegex(ValueError, "Missing source frame_count"):
            compile_controller(self.bundle, 710, timeline)

    def test_projectile_hit_write_and_opponent_goto_are_source_events(self):
        _, metadata = compile_controller(self.bundle, 710, self.timeline)
        hook = next(item for item in metadata["projectile_hooks"] if item["placement_frame"] == 887)
        projectile = hook["projectile"]
        self.assertEqual(projectile["on_hit_events"], [
            {"op": "write", "field": "Cbshit", "operator": "=", "value": True},
            {"op": "goto", "target": "opponent", "action": 2, "label": "被打", "play": True},
        ])

    def test_hit_events_preserve_source_order(self):
        source = """onClipEvent(enterFrame){
if(this.hitTest(_root.game[\"p\" + _parent.pn].mc.bdmn))
{
  if(_root.game[\"p\" + _parent.pn].mc.动作 == 2)
  {
    _root.game[\"p\" + _parent.pn].mc.gotoAndPlay(\"被打\");
  }
  _parent.Cbshit = true;
}
}"""
        motion = parse_projectile_motion(source)
        self.assertEqual([event["op"] for event in motion["on_hit_events"]], ["goto", "write"])

    def test_parent_write_outside_hit_branch_fails_closed(self):
        source = """onClipEvent(enterFrame){
_parent.Cbshit = true;
if(this.hitTest(_root.game[\"p\" + _parent.pn].mc.bdmn)) { }
}"""
        with self.assertRaisesRegex(ValueError, "outside hitTest"):
            parse_projectile_motion(source)

    def test_nested_parent_write_fails_closed(self):
        source = """onClipEvent(enterFrame){
if(this.hitTest(_root.game[\"p\" + _parent.pn].mc.bdmn))
{
  if(_root.zhanting == false) { _parent.Cbshit = true; }
}
}"""
        with self.assertRaisesRegex(ValueError, "Nested projectile parent write"):
            parse_projectile_motion(source)

    def test_local_hit_flag_declaration_and_conditional_jump_are_retained(self):
        compiled = compile_context(self.bundle, self.timeline)
        declaration = next(item for item in compiled["frame_writes"]["864"] if item["field"] == "Cbshit")
        self.assertEqual((declaration["field"], declaration["value"]), ("Cbshit", False))
        branch = compiled["frame_calls"]["900"][0]
        self.assertEqual(branch["conditions"], [{
            "field": "Cbshit", "operator": "eq", "value": True,
        }])
        self.assertEqual(branch["calls"], [
            {"op": "timeline_goto", "label": "超必杀2", "play": False},
            {"op": "timeline_play"},
        ])

    def test_root_rename_is_fifo_event_with_display_list_generation(self):
        compiled = compile_context(self.bundle, self.timeline)
        event = next(
            item for item in compiled["frame_calls"]["821"]
            if item["op"] == "root_clip_rename"
        )
        self.assertEqual(
            {key: event[key] for key in (
                "source_name", "instance_name", "depth", "character_id", "placed_frame",
                "frame", "line",
            )},
            {
                "source_name": "dogs", "instance_name": "sbsatm", "depth": 28,
                "character_id": 488, "placed_frame": 814, "frame": 821, "line": 1,
            },
        )

    def test_root_rename_old_name_is_undefined_but_current_name_can_rename_again(self):
        placement = {"depth": 28, "character_id": 488, "placed_frame": 10, "name": "dogs"}
        frames = {frame: {"display_list": [placement]} for frame in range(10, 14)}
        history = []
        self.assertEqual(
            _root_clip_rename_event(
                'dogs._name = "sbsatm";', "frame_11.as", 11, frames, history
            )[0]["instance_name"],
            "sbsatm",
        )
        # The static display list still says dogs, but the old source variable
        # is undefined after the first assignment.
        self.assertEqual(
            _root_clip_rename_event(
                'dogs._name = "other";', "frame_12.as", 12, frames, history
            ),
            [],
        )
        self.assertEqual(
            _root_clip_rename_event(
                'sbsatm._name = "other";', "frame_12.as", 12, frames, history
            )[0]["instance_name"],
            "other",
        )
if __name__ == "__main__":
    unittest.main()
