import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
from build_combat_model import parse_projectile_initialization, resolve_special_cost


class SpecialCostFallthroughTests(unittest.TestCase):
    def _case(self, *, span=(454, 454), labels=("空中必杀",), path=None, source=""):
        fighter = {"actions": {"special": {"必杀": {"start_frame": span[0], "end_frame": span[1]}},
                                "extended_actions": {"空中必杀": {"start_frame": 455, "end_frame": 500}}}}
        timeline = {"frames": [{"frame": 455, "labels": list(labels)}]}
        script_path = path or "DefineSprite_631/frame_455/DoAction.as"
        bundle = {"scripts": [{"path": script_path, "source": source or "动作 = 3;\nql -= 100;"}]}
        scripts = []
        return fighter, timeline, bundle, scripts

    def test_byakuya_direct_special_fallthrough_cost(self):
        case = self._case()
        result, match = resolve_special_cost(*case, 631, "必杀")
        self.assertEqual((result["frame"], match["cost"]), (455, "100"))

    def test_next_label_name_does_not_change_natural_fallthrough(self):
        case = self._case(labels=("站立",))
        result, match = resolve_special_cost(*case, 631, "必杀")
        self.assertEqual((result["frame"], match["cost"]), (455, "100"))

    def test_multiframe_special_does_not_donate_cost(self):
        with self.assertRaisesRegex(ValueError, "Expected one energy cost"):
            resolve_special_cost(*self._case(span=(454, 455)), 631, "必杀")

    def test_clip_action_at_boundary_does_not_donate_cost(self):
        with self.assertRaisesRegex(ValueError, "Expected one energy cost"):
            resolve_special_cost(*self._case(path="DefineSprite_631/frame_455/PlaceObject2_16_1/CLIPACTIONRECORD onClipEvent(load).as"), 631, "必杀")

    def test_terminated_special_does_not_donate_cost(self):
        case = self._case()
        case[3].append({"action": "必杀", "source": "stop();", "path": "DefineSprite_631/frame_454/DoAction.as"})
        with self.assertRaisesRegex(ValueError, "Expected one energy cost"):
            resolve_special_cost(*case, 631, "必杀")

    def test_original_two_frame_aliases_find_actual_cost(self):
        import json
        for fighter_id, sprite, start in [("yihu", 1672, 537), ("rifagu", 951, 566)]:
            with self.subTest(fighter=fighter_id):
                bundle = json.loads((ROOT / f"scripts/fighter/{fighter_id}.json").read_text())
                fighter = {"actions": {"special": {"必杀": {"start_frame": start, "end_frame": start}}}}
                timeline = {"frames": [{"frame": start + 1, "events": [], "changes": []},
                                       {"frame": start + 2, "events": [{"type": "action_bytecode"}]}]}
                result, match = resolve_special_cost(fighter, timeline, bundle, [], sprite, "必杀")
                self.assertEqual((result["frame"], match["cost"]), (start + 2, "100"))

    def test_blank_frame_cannot_hide_bytecode_or_clip_actions(self):
        for extra in [{"events": [{"type": "action_bytecode"}]},
                      {"changes": [{"clip_actions": [{"event": "load"}]}]}]:
            with self.subTest(extra=extra):
                case = self._case(path="DefineSprite_631/frame_456/DoAction.as")
                case[1]["frames"] = [{"frame": 455, **extra}, {"frame": 456}]
                with self.assertRaisesRegex(ValueError, "Expected one energy cost"):
                    resolve_special_cost(*case, 631, "必杀")

    def test_fallthrough_rejects_conditional_cost_and_intervening_actions(self):
        for source in ["if(ok){ql -= 100;}", "stop(); ql -= 100;", "foo(); ql -= 100;",
                       'gotoAndPlay("必杀"); ql -= 100;']:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "Expected one energy cost"):
                    resolve_special_cost(*self._case(source=source), 631, "必杀")
        case = self._case(source="动作 = 3;")
        case[1]["frames"].append({"frame": 456})
        case[2]["scripts"].append({"path": "DefineSprite_631/frame_456/DoAction.as", "source": "ql -= 100;"})
        with self.assertRaisesRegex(ValueError, "Expected one energy cost"):
            resolve_special_cost(*case, 631, "必杀")

    def test_missing_timeline_frame_cannot_be_assumed_empty(self):
        case = self._case(path="DefineSprite_631/frame_456/DoAction.as")
        case[1]["frames"] = [{"frame": 456}]
        with self.assertRaisesRegex(ValueError, "Expected one energy cost"):
            resolve_special_cost(*case, 631, "必杀")

    def test_projectile_load_compiles_undeclared_as2_locals(self):
        result = parse_projectile_initialization(
            "onClipEvent(load){\n played = 0;\n movspeed = _parent.speed;\n}"
        )
        self.assertEqual(result["initial_variables"], {"played": 0})
        self.assertEqual(result["initial_speed_field"], "speed")

    def test_projectile_load_rejects_unknown_statement(self):
        with self.assertRaisesRegex(ValueError, "Uncompiled projectile load"):
            parse_projectile_initialization("onClipEvent(load){ played = 0; foo(); }")


if __name__ == "__main__":
    unittest.main()
