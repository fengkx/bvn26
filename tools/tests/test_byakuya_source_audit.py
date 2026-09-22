"""Regression checks for the Byakuya source-first audit."""
import json
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ByakuyaSourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads((ROOT / "evidence/characters/byakuya/source-audit.json").read_text())

    def test_locked_source_identity_and_base_placement(self):
        self.assertEqual(self.audit["sources"]["swf"]["path"], "game/fighter/Byakuya.swf")
        self.assertEqual(
            self.audit["sources"]["swf"]["sha256"],
            "c590f9ca2aea152d26aea8d6a10c4ee31a2019d9798c637820f145feef13b52f",
        )
        self.assertEqual(self.audit["root_placements"][0], {"frame": 1, "depth": 1, "character_id": 631})

    def test_base_timeline_and_deferred_bankai_boundary(self):
        timeline = self.audit["timeline"]
        self.assertEqual(timeline["name"], "sprite_631")
        self.assertEqual(timeline["declared_frames"], 1115)
        self.assertEqual(self.audit["scope"]["excluded_label"], "万解")
        self.assertEqual(self.audit["scope"]["excluded_start_frame"], 1105)

    def test_source_first_audit_does_not_claim_original_parity(self):
        self.assertEqual(self.audit["status"], "source_inventory_not_behavior_acceptance")
        self.assertIn("Not available yet", self.audit["source_first"]["q5_same_input"])

    def test_regenerator_keeps_bundle_hash_in_sync(self):
        path = ROOT / "scripts/fighter/Byakuya.json"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(actual, self.audit["sources"]["script_bundle"]["sha256"])

    def test_special_cost_boundary_is_retained(self):
        scripts = {item["frame"]: item for item in self.audit["special_frame_scripts"]}
        self.assertIn(455, scripts)
        self.assertIn("ql -= 100", scripts[455]["source"])
        spans = self.audit["timeline"]["spans"]
        self.assertEqual(spans["必杀"], {"start_frame": 454, "end_frame": 454})
        self.assertEqual(spans["空中必杀"]["start_frame"], 455)

    def test_dynamic_nested_controller_inventory_retains_source_ids(self):
        placements = self.audit["nested_controller_placements"]
        self.assertTrue(any(item["character_id"] == 16 and item["frame"] == 1 for item in placements))
        self.assertTrue(any(item["character_id"] == 69 for item in placements))
        self.assertTrue(any(item["character_id"] == 2 for item in placements))

    def test_generated_timeline_and_combat_keep_source_identity(self):
        timeline = json.loads((ROOT / "data/slices/Byakuya-base.timeline.json").read_text())
        combat = json.loads((ROOT / "data/actions/Byakuya-base.json").read_text())
        self.assertEqual(timeline["source_swf"]["path"], "game/fighter/Byakuya.swf")
        self.assertEqual(timeline["sprite_id"], 631)
        self.assertEqual(combat["source"]["fighter_slice"], "data/slices/Byakuya-base.json")
        self.assertEqual(combat["source"]["script_bundle"], "scripts/fighter/Byakuya.json")
        self.assertEqual(combat["fighter_id"], "白哉")
        self.assertEqual(combat["movement"]["speed_per_tick"], 12)


if __name__ == "__main__":
    unittest.main()
