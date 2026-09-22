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
