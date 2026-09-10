"""Source-first regression checks for the Renji base-form import."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RenjiImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.slice = json.loads((ROOT / "data/slices/Renji-base.json").read_text())
        cls.timeline = json.loads(
            (ROOT / "data/slices/Renji-base.timeline.json").read_text()
        )
        cls.model = json.loads((ROOT / "data/actions/Renji-base.json").read_text())
        cls.bundle = json.loads((ROOT / "scripts/fighter/Renji.json").read_text())
        cls.generated = json.loads(
            (ROOT / "godot/generated/fighters/renji/combat.json").read_text()
        )
        cls.fixture = json.loads(
            (ROOT / "evidence/combat/renji-base/source-fixture.json").read_text()
        )

    def test_base_form_identity_and_source_hashes_are_retained(self):
        self.assertEqual(self.slice["fighter_id"], "恋次")
        self.assertEqual(self.slice["form_frame"], 1)
        self.assertEqual(self.slice["source"]["timeline_symbol_id"], 717)
        self.assertEqual(self.model["source"]["timeline_symbol_id"], 717)
        self.assertEqual(self.timeline["sprite_id"], 717)
        self.assertEqual(self.timeline["source_swf"]["path"], "game/fighter/Renji.swf")
        self.assertEqual(
            self.timeline["source_swf"]["sha256"],
            "7505e9591f46ba1d05bb03fff9450d52583804022a08ba3bb7a0ecfb21cb116a",
        )

    def test_source_action_spans_cover_original_labels(self):
        movement = self.slice["actions"]["movement"]
        self.assertEqual(movement["站立"], {"start_frame": 1, "end_frame": 9})
        self.assertEqual(movement["走"], {"start_frame": 10, "end_frame": 19})
        self.assertEqual(movement["跳"], {"start_frame": 40, "end_frame": 55})
        self.assertEqual(movement["落2"], {"start_frame": 89, "end_frame": 114})
        self.assertEqual(
            self.slice["actions"]["ground_combo"]["砍1"],
            {"start_frame": 173, "end_frame": 191},
        )
        self.assertEqual(
            self.slice["actions"]["ground_combo"]["砍3"],
            {"start_frame": 215, "end_frame": 244},
        )
        self.assertEqual(
            self.slice["actions"]["special"]["必杀"],
            {"start_frame": 502, "end_frame": 585},
        )

    def test_complete_base_move_fixture_matches_source_slice(self):
        source_actions = {}
        for group in self.slice["actions"].values():
            source_actions.update(group)
        self.assertEqual(
            {
                label: [span["start_frame"], span["end_frame"]]
                for label, span in source_actions.items()
            },
            self.fixture["actions"],
        )
        self.assertEqual(self.fixture["timeline_frame_count"], self.timeline["frame_count"])
        self.assertEqual(self.fixture["timeline_symbol_id"], self.timeline["sprite_id"])

        catalog = {
            entry["label"]: entry
            for entry in self.model["command_catalog"]["entries"]
            if entry.get("start_frame") is not None
        }
        for label, (start, end) in self.fixture["actions"].items():
            if label not in catalog:
                continue
            self.assertEqual(catalog[label]["start_frame"], start, label)
            self.assertEqual(catalog[label]["end_frame"], end, label)

    def test_super_and_hit_lifecycle_is_compiled_from_source_frames(self):
        self.assertEqual(self.model["face_labels"], ["恋次1", "恋次2", "恋次3"])
        events = self.model["super_events"]
        self.assertEqual(
            [(e["action"], e["frame"], e["op"], e.get("face_label")) for e in events],
            [
                ("必杀", 506, "super_start", "恋次1"),
                ("必杀", 539, "super_end", None),
                ("上必杀", 592, "super_start", "恋次2"),
                ("上必杀", 624, "super_end", None),
                ("超必杀", 680, "super_start", "恋次3"),
                ("超必杀", 834, "super_end", None),
            ],
        )
        self.assertEqual(self.model["hits_reset_frames"], [{"sprite_id": 717, "frame": 2, "source_path": "DefineSprite_717/frame_2/DoAction.as"}])
        self.assertEqual(
            [(item["frame"], item["flying"]) for item in self.model["on_be_hit_frames"]],
            [(970, False), (983, True)],
        )
        self.assertEqual(self.model["hurt"]["stop_frame"], 975)
        self.assertEqual(self.model["death"]["knockdown_stop_frame"], 1008)
        self.assertEqual(
            [
                {
                    key: event[key]
                    for key in ("action", "frame", "op", "kind", "face_label")
                    if key in event
                }
                for event in events
            ],
            self.fixture["super_events"],
        )
        self.assertEqual(
            [
                [event["frame"], event["flying"]]
                for event in self.model["on_be_hit_frames"]
            ],
            self.fixture["hit_lifecycle"]["on_be_hit"],
        )

    def test_generated_combat_is_the_same_compiled_model(self):
        self.assertEqual(self.generated["fighter_id"], self.model["fighter_id"])
        self.assertEqual(self.generated["source"], self.model["source"])
        self.assertEqual(self.generated["attacks_by_form"], self.model["attacks_by_form"])
        self.assertEqual(self.generated["command_catalog"], self.model["command_catalog"])

    def test_source_scripts_include_new_place_and_move_sensitive_callbacks(self):
        paths = {record["path"] for record in self.bundle["scripts"]}
        self.assertIn(
            "DefineSprite_717/frame_971/PlaceObject2_16_28/CLIPACTIONRECORD onClipEvent(enterFrame).as",
            paths,
        )
        self.assertIn(
            "DefineSprite_717/frame_42/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as",
            paths,
        )
        self.assertIn("DefineSprite_717/frame_506/DoAction.as", paths)
        self.assertIn("DefineSprite_717/frame_592/DoAction.as", paths)
        self.assertIn("DefineSprite_717/frame_680/DoAction.as", paths)


if __name__ == "__main__":
    unittest.main()
