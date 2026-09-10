import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from kakashi_source_audit import build_audit  # noqa: E402


class KakashiSourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads(
            (ROOT / "evidence/combat/kakashi-source-audit.json").read_text(encoding="utf-8")
        )

    def test_source_identity_and_base_form(self):
        fighter = self.audit["fighter"]
        self.assertEqual(fighter["id"], "卡卡西")
        self.assertEqual(fighter["source_swf"], "game/fighter/Kakashi.swf")
        self.assertEqual(fighter["timeline_symbol_id"], 710)
        self.assertEqual(fighter["form_frame"], 1)
        self.assertEqual(fighter["assist"], "我爱罗")

    def test_every_source_frame_is_indexed(self):
        timeline = self.audit["timeline"]
        frames = timeline["frame_index"]
        self.assertEqual(timeline["frame_count"], 1385)
        self.assertEqual([frame["frame"] for frame in frames], list(range(1, 1386)))
        self.assertEqual(frames[1]["do_action"][0]["path"], "DefineSprite_710/frame_2/DoAction.as")
        self.assertEqual(frames[1]["do_action"][0]["source"].strip(), "hits = 0;")

    def test_source_owned_combat_and_super_invariants(self):
        self.assertEqual(self.audit["movement_constants"]["speed_per_tick"], 8)
        self.assertEqual(self.audit["movement_constants"]["jump_power"], 18)
        self.assertEqual(self.audit["hits_reset_frames"], [2])
        self.assertEqual(self.audit["defence_frames"][0]["argument"], 2)
        self.assertEqual([item["frame"] for item in self.audit["be_hit_frames"]], [1117, 1130])
        self.assertEqual([item["face_label"] for item in self.audit["super_events"]], ["卡卡西1", "卡卡西2", "卡卡西3"])
        self.assertEqual([item["freeze"] for item in self.audit["super_events"]], ["bsd", "bsd", "cbsd"])
        self.assertGreaterEqual(len(self.audit["attacks"]), 20)
        self.assertEqual(self.audit["attacks"]["cbs"]["zl"], "5")

    def test_generated_evidence_matches_current_source(self):
        current = build_audit(ROOT)
        self.assertEqual(current["fighter"], self.audit["fighter"])
        self.assertEqual(current["timeline"]["frame_index"], self.audit["timeline"]["frame_index"])
        self.assertEqual(current["attacks"], self.audit["attacks"])


if __name__ == "__main__":
    unittest.main()
