import importlib.util
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


inspect_swf = load_module("inspect_swf", ROOT / "tools/inspect_swf.py")
source_inventory = load_module(
    "source_inventory", ROOT / "tools/importer/build_source_inventory.py"
)
fighter_slice = load_module(
    "fighter_slice", ROOT / "tools/importer/extract_fighter_slice.py"
)
timeline_geometry = load_module(
    "timeline_geometry", ROOT / "tools/importer/extract_timeline_geometry.py"
)
combat_model = load_module(
    "combat_model", ROOT / "tools/importer/build_combat_model.py"
)


def tag(code: int, payload: bytes = b"") -> bytes:
    assert len(payload) < 63
    return struct.pack("<H", code << 6 | len(payload)) + payload


def minimal_swf(tags: bytes) -> bytes:
    rect = b"\x08\x00"
    body = rect + struct.pack("<HH", 30 * 256, 1) + tags
    return b"FWS" + bytes([8]) + struct.pack("<I", 8 + len(body)) + body


class InspectSwfTests(unittest.TestCase):
    def test_reports_place_object_clip_actions(self):
        place_object = tag(26, b"\x80\x01\x00")
        data = minimal_swf(place_object + tag(1) + tag(0))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clip-action.swf"
            path.write_bytes(data)
            result = inspect_swf.inspect(path)

        self.assertEqual(
            result["clip_action_tags"],
            [{"timeline": "root", "frame": 1, "tag": 26, "bytes": 3}],
        )


class ScriptClassificationTests(unittest.TestCase):
    def test_clip_action_is_never_folded_into_frame_action(self):
        event_type, category = source_inventory.classify_script(
            "frame_1/PlaceObject2_1_1/CLIPACTIONRECORD onClipEvent(enterFrame).as",
            "if (this.hitTest(_root.player)) { _root.player.hp -= 10; }",
        )
        self.assertEqual(event_type, "clip_action")
        self.assertEqual(category, "collision_or_damage")

    def test_unknown_frame_action_remains_unresolved(self):
        event_type, category = source_inventory.classify_script(
            "frame_1/DoAction.as", "foo = bar;"
        )
        self.assertEqual(event_type, "frame_action")
        self.assertEqual(category, "unresolved_semantics")

    def test_4399_package_is_an_excluded_platform_adapter(self):
        event_type, category = source_inventory.classify_script(
            "__Packages/AS2_4399_API/Bridge.as", "class Bridge {}"
        )
        self.assertEqual(event_type, "init_action_class")
        self.assertEqual(category, "platform_adapter")


class FighterSliceTests(unittest.TestCase):
    def test_base_form_symbols_come_from_root_frame_one(self):
        naruto = fighter_slice.extract_slice(ROOT, "鸣人")
        ichigo = fighter_slice.extract_slice(ROOT, "一护")
        self.assertEqual(naruto["source"]["timeline_symbol_id"], 764)
        self.assertEqual(ichigo["source"]["timeline_symbol_id"], 638)

    def test_movement_and_combo_values_come_from_base_form_code(self):
        naruto = fighter_slice.extract_slice(ROOT, "鸣人")
        ichigo = fighter_slice.extract_slice(ROOT, "一护")
        self.assertEqual(naruto["movement_constants"]["speed_per_tick"], 8)
        self.assertEqual(ichigo["movement_constants"]["speed_per_tick"], 6)
        self.assertEqual(
            [naruto["hit_parameters"]["attacks"][key]["damage"] for key in ("k1", "k2", "k3")],
            [15, 30, 40],
        )
        self.assertEqual(
            [ichigo["hit_parameters"]["attacks"][key]["damage"] for key in ("k1", "k2", "k3")],
            [40, 50, 70],
        )

    def test_target_action_boundaries_are_swf_labels(self):
        naruto = fighter_slice.extract_slice(ROOT, "鸣人")
        ichigo = fighter_slice.extract_slice(ROOT, "一护")
        self.assertEqual(
            naruto["actions"]["ground_combo"],
            {
                "砍1": {"start_frame": 170, "end_frame": 186},
                "砍2": {"start_frame": 187, "end_frame": 206},
                "砍3": {"start_frame": 207, "end_frame": 235},
            },
        )
        self.assertEqual(
            ichigo["actions"]["ground_combo"],
            {
                "砍1": {"start_frame": 173, "end_frame": 189},
                "砍2": {"start_frame": 190, "end_frame": 209},
                "砍3": {"start_frame": 210, "end_frame": 231},
            },
        )
        self.assertEqual(
            naruto["actions"]["hurt"],
            {"被打": {"start_frame": 1014, "end_frame": 1026}},
        )
        self.assertEqual(
            ichigo["actions"]["hurt"],
            {"被打": {"start_frame": 738, "end_frame": 750}},
        )
        self.assertEqual(
            naruto["actions"]["special"],
            {
                "必杀": {"start_frame": 504, "end_frame": 542},
                "必杀1": {"start_frame": 543, "end_frame": 585},
                "必杀0": {"start_frame": 586, "end_frame": 608},
            },
        )
        self.assertEqual(
            ichigo["actions"]["special"],
            {"必杀": {"start_frame": 446, "end_frame": 527}},
        )


class TimelineGeometryTests(unittest.TestCase):
    def test_place_modify_remove_preserves_display_list_state(self):
        root = ET.fromstring(
            """<swf _xmlExportMajor="2" _xmlExportMinor="2">
            <tags>
            <item type="DefineShape3Tag" shapeId="9">
              <shapeBounds Xmin="0" Ymin="-20" Xmax="40" Ymax="60"/>
            </item>
            <item type="DefineSpriteTag" spriteId="10" frameCount="1">
              <subTags>
                <item type="PlaceObject2Tag" depth="1" characterId="9" placeFlagMove="false">
                  <matrix translateX="5" translateY="10"/>
                </item>
                <item type="ShowFrameTag"/>
              </subTags>
            </item>
            <item type="DefineSpriteTag" spriteId="7" frameCount="3">
              <subTags>
                <item type="FrameLabelTag" name="start"/>
                <item type="PlaceObject2Tag" depth="2" characterId="9" placeFlagMove="false">
                  <matrix translateX="20" translateY="-40"/>
                </item>
                <item type="ShowFrameTag"/>
                <item type="PlaceObject2Tag" depth="3" characterId="10" placeFlagMove="false"/>
                <item type="PlaceObject2Tag" depth="2" placeFlagMove="true" ratio="5"/>
                <item type="ShowFrameTag"/>
                <item type="RemoveObject2Tag" depth="2"/>
                <item type="ShowFrameTag"/>
              </subTags>
            </item></tags></swf>"""
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "timeline.xml"
            ET.ElementTree(root).write(path, encoding="unicode")
            result = timeline_geometry.extract_frames(path, 7)

        self.assertEqual(result["frames"][0]["labels"], ["start"])
        self.assertEqual(
            result["frames"][1]["display_list"],
            [
                {
                    "depth": 2,
                    "character_id": 9,
                    "matrix": {"translateX": 20, "translateY": -40},
                    "placed_frame": 1,
                    "ratio": 5,
                },
                {"depth": 3, "character_id": 10, "placed_frame": 2},
            ],
        )
        self.assertEqual(
            result["frames"][2]["display_list"],
            [{"depth": 3, "character_id": 10, "placed_frame": 2}],
        )
        self.assertEqual(
            result["definitions"],
            [
                {
                    "character_id": 9,
                    "type": "DefineShape3Tag",
                    "shape_bounds_twips": {"Xmin": 0, "Ymin": -20, "Xmax": 40, "Ymax": 60},
                },
                {
                    "character_id": 10,
                    "type": "DefineSpriteTag",
                    "referenced_character_ids": [9],
                    "frame_count": 1,
                    "first_frame_display_list": [
                        {
                            "depth": 1,
                            "character_id": 9,
                            "matrix": {"translateX": 5, "translateY": 10},
                            "placed_frame": 1,
                        }
                    ],
                    "display_list_frames": [
                        [
                            {
                                "depth": 1,
                                "character_id": 9,
                                "matrix": {"translateX": 5, "translateY": 10},
                                "placed_frame": 1,
                            }
                        ]
                    ],
                },
            ],
        )


class CombatModelTests(unittest.TestCase):
    def load_model(self, fighter: str):
        return combat_model.build_model(
            ROOT / f"data/slices/{fighter}-base.json",
            ROOT / f"data/slices/{fighter}-base.timeline.json",
            ROOT / f"scripts/fighter/{fighter}.json",
        )

    def test_combo_windows_follow_persistent_clip_actions(self):
        naruto = self.load_model("minren")
        ichigo = self.load_model("yihu")
        self.assertEqual(
            [(item["from"], item["to"], item["start_frame"], item["end_frame"])
             for item in naruto["combo"]["transitions"]],
            [("砍1", "砍2", 176, 181), ("砍2", "砍3", 194, 202)],
        )
        self.assertEqual(
            [(item["from"], item["to"], item["start_frame"], item["end_frame"])
             for item in ichigo["combo"]["transitions"]],
            [("砍1", "砍2", 181, 184), ("砍2", "砍3", 198, 205)],
        )

    def test_attack_and_hurt_frames_come_from_display_and_as2(self):
        naruto = self.load_model("minren")
        ichigo = self.load_model("yihu")
        self.assertEqual(
            naruto["hitbox_windows"]["砍1"],
            [{"instance_name": "k1atm", "start_frame": 174, "end_frame": 176}],
        )
        self.assertEqual(
            naruto["hitbox_windows"]["砍2"],
            [{"instance_name": "k1atm", "start_frame": 191, "end_frame": 194}],
        )
        self.assertEqual(
            naruto["hitbox_windows"]["砍3"],
            [{"instance_name": "k2atm", "start_frame": 211, "end_frame": 214}],
        )
        self.assertEqual(
            ichigo["hitbox_windows"]["砍3"],
            [{"instance_name": "k3atm", "start_frame": 213, "end_frame": 215}],
        )
        self.assertEqual(naruto["hurt"]["stop_frame"], 1020)
        self.assertEqual(ichigo["hurt"]["stop_frame"], 744)
        self.assertEqual(naruto["action_exits"]["砍1"]["frame"], 182)
        self.assertEqual(ichigo["action_exits"]["必杀"]["frame"], 521)

    def test_special_chain_and_cost_are_source_driven(self):
        naruto = self.load_model("minren")
        ichigo = self.load_model("yihu")
        self.assertEqual(naruto["special"]["energy_cost"], 100)
        self.assertEqual(ichigo["special"]["energy_cost"], 100)
        self.assertEqual(
            [(item["from"], item["to"], item["frame"], item["condition"])
             for item in naruto["special"]["transitions"]],
            [
                ("必杀", "必杀1", 538, "source_condition"),
                ("必杀", "必杀0", 542, "always"),
                ("必杀1", "必杀0", 586, "timeline_fallthrough"),
            ],
        )
        self.assertEqual(ichigo["special"]["transitions"], [])


if __name__ == "__main__":
    unittest.main()
