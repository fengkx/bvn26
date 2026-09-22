import json
import unittest
from pathlib import Path

from tools.probes.hit_receive_observer import instrument_hit_receive, observer_schema


ROOT = Path(__file__).resolve().parents[2]


class HitReceiveObserverTests(unittest.TestCase):
    def _fighter_script(self, fighter: str) -> str:
        bundle = json.loads((ROOT / f"scripts/fighter/{fighter}.json").read_text())
        matches = [script["source"] for script in bundle["scripts"]
                   if "function getHitObj(" in script["source"]]
        self.assertTrue(matches, fighter)
        return matches[0]

    def test_hit_test_is_evaluated_once_and_original_packet_fields_remain(self):
        source = self._fighter_script("lee")
        observed = instrument_hit_receive(source, "fighter/lee#DefineSprite_2/frame_1/DoAction.as")
        self.assertEqual(observed.count("this.hitTest(_loc4_)"), 1)
        self.assertIn('"source_hit_test"', observed)
        self.assertIn('String(ppw[_loc2_ + "dz"])', observed)
        self.assertIn("zl:ppw[_loc2_ + \"zl\"]", observed)
        self.assertIn('"source_guard_packet"', observed)
        self.assertIn('"source_hit_packet"', observed)
        self.assertIn('(_loc2_.zl > 10 ? "break" : "blocked"));', observed)
        self.assertIn('if(_parent.bdzl > 10)', observed)
        self.assertIn('gotoAndPlay("防住")', observed)

    def test_hook_is_scoped_to_selected_fighter_bundle(self):
        source = self._fighter_script("lee")
        self.assertIs(instrument_hit_receive(source, "main#frame_8/DoAction.as"), source)
        self.assertIs(instrument_hit_receive(source, "fighter/fz/kon#frame_1/DoAction.as"), source)

    def test_hook_fails_closed_if_source_shape_changes(self):
        source = self._fighter_script("lee").replace("if(this.hitTest(_loc4_))", "if(this.hitTest(_loc3_))")
        with self.assertRaisesRegex(ValueError, "getHitObj hitTest"):
            instrument_hit_receive(source, "fighter/lee#DefineSprite_2/frame_1/DoAction.as")

    def test_schema_mentions_geometry_and_source_decision(self):
        schema = observer_schema()
        self.assertEqual(len(schema["source_hit_test"]), 61)
        self.assertIn("attack_bounds_xmin", schema["source_hit_test"])
        self.assertIn("target_bdmn_bounds_xmin", schema["source_hit_test"])
        self.assertIn("source_branch_zl_gt_10", schema["source_guard_packet"])


if __name__ == "__main__":
    unittest.main()
