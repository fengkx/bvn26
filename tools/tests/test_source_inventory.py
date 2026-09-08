import importlib.util
import json
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
helper_model = load_module(
    "helper_model", ROOT / "tools/importer/build_helper_model.py"
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

    def test_root_timeline_extracts_display_list(self):
        root = ET.fromstring(
            """<swf _xmlExportMajor="3" _xmlExportMinor="2" frameCount="2">
            <tags>
            <item type="DefineShapeTag" shapeId="4">
              <shapeBounds Xmin="0" Ymin="0" Xmax="20" Ymax="20"/>
            </item>
            <item type="PlaceObject2Tag" depth="1" characterId="4" name="atm1" placeFlagMove="false">
              <matrix translateX="40" translateY="0"/>
            </item>
            <item type="ShowFrameTag"/>
            <item type="PlaceObject2Tag" depth="1" placeFlagMove="true">
              <matrix translateX="80" translateY="0"/>
            </item>
            <item type="ShowFrameTag"/>
            </tags></swf>"""
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "helper.xml"
            ET.ElementTree(root).write(path, encoding="unicode")
            result = timeline_geometry.extract_frames(path)

        self.assertEqual(result["timeline"], "root")
        self.assertEqual(result["sprite_id"], 0)
        self.assertEqual(result["frame_count"], 2)
        self.assertEqual(result["frames"][0]["display_list"][0]["name"], "atm1")
        self.assertEqual(result["frames"][1]["display_list"][0]["matrix"]["translateX"], 80)

    def test_sprite_extract_keeps_root_mc_wrapper_matrix(self):
        root = ET.fromstring(
            """<swf _xmlExportMajor="3" _xmlExportMinor="2" frameCount="1">
            <tags>
            <item type="DefineShape3Tag" shapeId="9">
              <shapeBounds Xmin="0" Ymin="-20" Xmax="40" Ymax="60"/>
            </item>
            <item type="DefineSpriteTag" spriteId="7" frameCount="1">
              <subTags>
                <item type="PlaceObject2Tag" depth="1" characterId="9" placeFlagMove="false">
                  <matrix translateX="20" translateY="-40"/>
                </item>
                <item type="ShowFrameTag"/>
              </subTags>
            </item>
            <item type="PlaceObject2Tag" depth="1" characterId="7" name="mc" placeFlagMove="false">
              <matrix hasScale="true" scaleX="1.0" scaleY="1.0007019" translateX="-13" translateY="-478"/>
            </item>
            <item type="ShowFrameTag"/>
            </tags></swf>"""
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fighter.xml"
            ET.ElementTree(root).write(path, encoding="unicode")
            result = timeline_geometry.extract_frames(path, 7)

        self.assertEqual(
            result["wrapper"],
            {
                "name": "mc",
                "character_id": 7,
                "root_frame": 1,
                "depth": 1,
                "matrix": {
                    "hasScale": "true",
                    "scaleX": 1.0,
                    "scaleY": 1.0007019,
                    "translateX": -13,
                    "translateY": -478,
                },
            },
        )


class CombatModelTests(unittest.TestCase):
    def load_model(self, fighter: str):
        return combat_model.build_model(
            ROOT / f"data/slices/{fighter}-base.json",
            ROOT / f"data/slices/{fighter}-base.timeline.json",
            ROOT / f"scripts/fighter/{fighter}.json",
        )

    def test_on_jumping_windows_follow_clip_lifetime(self):
        naruto = self.load_model("minren")
        ichigo = self.load_model("yihu")
        self.assertEqual(
            [(item["action"], item["start_frame"], item["end_frame"], item["step"])
             for item in naruto["jump_windows"]],
            [
                ("跳", 42, 49, 1),
                ("跳", 50, 55, 2),
                ("落", 56, 71, 3),
                ("跳2", 72, 82, 4),
                ("跳2", 83, 88, 5),
                ("落2", 89, 114, 6),
            ],
        )
        self.assertEqual(
            [(item["action"], item["start_frame"], item["end_frame"], item["step"])
             for item in ichigo["jump_windows"]],
            [
                ("跳", 42, 49, 1),
                ("跳", 50, 55, 2),
                ("落", 56, 71, 3),
                ("跳2", 72, 82, 4),
                ("跳2", 83, 88, 5),
                ("落2", 89, 114, 6),
            ],
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
        self.assertEqual(naruto["death"]["launch_label"], "击飞")
        self.assertEqual(naruto["death"]["down_label"], "击落地")
        self.assertEqual(naruto["death"]["knockdown_stop_frame"], 1053)
        self.assertEqual(ichigo["death"]["launch_label"], "击飞")
        self.assertEqual(ichigo["death"]["down_label"], "击落地")
        self.assertEqual(ichigo["death"]["knockdown_stop_frame"], 777)
        self.assertEqual(
            naruto["hit_priority"]["instances"][:7],
            ["tkatm", "tk1atm", "tk2atm", "tk3atm", "tk4atm", "tk5atm", "tzatm"],
        )
        self.assertLess(
            naruto["hit_priority"]["instances"].index("zh3atm"),
            naruto["hit_priority"]["instances"].index("zh32atm"),
        )
        self.assertIn("DefineSprite_", naruto["hit_priority"]["source_path"])
        self.assertEqual(naruto["action_exits"]["砍1"]["frame"], 182)
        self.assertEqual(ichigo["action_exits"]["必杀"]["frame"], 521)
        self.assertEqual(naruto["action_exits"]["招3"]["frame"], 491)
        self.assertEqual(naruto["action_exits"]["招3"]["target"], "落")
        self.assertEqual(ichigo["action_exits"]["跳招"]["target"], "落2")
        self.assertNotIn("走", naruto["action_exits"])
        self.assertEqual(
            combat_model.parse_unconditional_exit('gotoAndStop("落");\r\nplay();\r\n'),
            "落",
        )
        self.assertIsNone(
            combat_model.parse_unconditional_exit(
                'if(hp > 0)\r\n{\r\n   gotoAndStop("必杀1");\r\n   play();\r\n}\r\n'
            )
        )

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

    def test_command_catalog_lists_every_timeline_label(self):
        naruto = self.load_model("minren")
        ichigo = self.load_model("yihu")
        catalog = naruto["command_catalog"]
        self.assertEqual(catalog["id_convention"], "source_frame_label")
        self.assertEqual(catalog["format"], "bvn26-command-catalog-v1")
        labels = {item["label"] for item in catalog["entries"]}
        slice_data = json.loads((ROOT / "data/slices/minren-base.json").read_text(encoding="utf-8"))
        for group in slice_data["actions"].values():
            for label in group:
                self.assertIn(label, labels)
        self.assertIn("万解", labels)
        self.assertIn("砍4", labels)
        self.assertIn("空中必杀", labels)
        by_label = {item["label"]: item for item in catalog["entries"]}
        self.assertEqual(by_label["砍1"]["implementation"], "wired")
        self.assertEqual(by_label["砍1"]["slot"], "nornalhit")
        self.assertEqual(by_label["万解"]["implementation"], "wired")
        self.assertEqual(by_label["万解"]["slot"], "wankai")
        self.assertEqual(by_label["空中必杀"]["implementation"], "missing_timeline")
        self.assertFalse(any(gap["label"] == "万解" for gap in catalog["gaps"] if gap["kind"] == "command"))
        self.assertTrue(
            any(
                gap["from"] == "砍3" and gap["to"] == "砍4"
                for gap in catalog["gaps"]
                if gap["kind"] == "cancel"
            )
        )
        ichigo_labels = {item["label"] for item in ichigo["command_catalog"]["entries"]}
        self.assertIn("招21", ichigo_labels)
        self.assertIn("万解", ichigo_labels)
        self.assertEqual(
            ichigo["command_catalog"]["predicates"]["nornalhit"]["buttons_all"],
            ["attack"],
        )

    def test_motion_windows_and_projectiles_follow_clip_actions(self):
        naruto = self.load_model("minren")
        ichigo = self.load_model("yihu")
        slash1 = next(
            window for window in naruto["motion_windows"] if window["action"] == "砍1"
        )
        self.assertEqual(
            (slash1["start_frame"], slash1["end_frame"], slash1["forward_speed_factor"]),
            (172, 175, 0.25),
        )
        self.assertTrue(slash1["round_forward"])
        skill1 = next(
            window for window in naruto["motion_windows"] if window["action"] == "砍技1"
        )
        self.assertEqual(skill1["forward_speed_factor"], 2.0)
        self.assertEqual(skill1["contact_cancel_to"], "砍技12")
        self.assertEqual(skill1["contact_instance"], "kj10atm")
        self.assertIn(
            {
                "from": "砍技1",
                "to": "砍技12",
                "frame": 291,
                "condition": "timeline_fallthrough",
            },
            naruto["timeline_fallthroughs"],
        )
        self.assertEqual(naruto["action_exits"]["砍技12"]["frame"], 313)
        self.assertEqual(naruto["action_exits"]["砍技12"]["target"], "站立")
        self.assertEqual(
            [
                (event["action"], event["frame"], event["op"], event["color_rgb24"])
                for event in naruto["presentation_events"]
                if event["action"] == "砍技12"
            ],
            [("砍技12", 292, "screen_flash", 1403539)],
        )
        spiral = next(
            window
            for window in naruto["motion_windows"]
            if window["action"] == "螺旋手里剑1"
        )
        self.assertEqual(spiral["vertical_speed_factor"], 1.0)
        self.assertEqual(spiral["land_cancel_to"], "超必杀2")
        self.assertEqual(
            [
                (
                    item["instance_name"],
                    item["start_frame"],
                    item["end_frame"],
                    item["speed_factor"],
                    item.get("on_hit_goto_frame"),
                    item.get("stop_frames"),
                )
                for item in naruto["projectiles"]
            ],
            [("zh1atm", 382, 403, 2.0, 5, [3, 11])],
        )
        self.assertEqual(naruto["projectiles"][0]["character_id"], 260)
        self.assertEqual(
            [
                (item["frame"], item["instance_name"])
                for item in naruto["projectiles"][0].get("rename_frames", [])
            ],
            [(5, "abcd")],
        )
        self.assertEqual(
            [
                (item["action"], item["frame"], item["helper_id"], item["start_frame"])
                for item in naruto["summon_events"]
            ],
            [("招换", 956, "我爱罗", 2)],
        )
        self.assertEqual(
            [
                (item["action"], item["frame"], item["helper_id"])
                for item in ichigo["summon_events"]
            ],
            [("招换", 657, "魂")],
        )
        rush = next(
            window for window in ichigo["motion_windows"] if window["action"] == "招2"
        )
        self.assertEqual(rush["forward_speed_factor"], 3.0)
        self.assertEqual(rush["contact_cancel_to"], "招21")
        self.assertEqual(rush["contact_instance"], "zh20atm")
        self.assertEqual(
            [item["instance_name"] for item in ichigo["projectiles"]],
            ["zh1atm", "zh1atm", "zh1atm"],
        )

    def test_helper_combat_follows_fz_scripts(self):
        gaara = helper_model.build_model(
            ROOT / "scripts/fighter/fz/woailuo.json",
            ROOT / "game/fighter/fz/woailuo.swf",
            "我爱罗",
        )
        kon = helper_model.build_model(
            ROOT / "scripts/fighter/fz/kon.json",
            ROOT / "game/fighter/fz/kon.swf",
            "魂",
        )
        self.assertEqual(gaara["simulation_hz"], 30)
        self.assertEqual(gaara["source"]["header_fps"], 30)
        self.assertEqual(gaara["start_frame"], 2)
        self.assertEqual(gaara["end_frame"], 85)
        self.assertEqual(gaara["hide_frames"], [85])
        self.assertEqual(gaara["attacks"]["atm1"]["damage"], 30)
        self.assertEqual(gaara["attacks"]["atm1"]["hitstun_ms"], 500)
        self.assertEqual(gaara["attacks"]["atm1"]["reaction_label"], "被打")
        self.assertEqual(kon["end_frame"], 102)
        self.assertEqual(kon["hide_frames"], [102])
        self.assertEqual(kon["attacks"]["atm1"]["damage"], 10)
        self.assertEqual(kon["attacks"]["atm1"]["hitstun_ms"], 300)
        self.assertEqual(
            [(item["frame"], item["delta"]) for item in kon["drain_events"]],
            [(72, -20.0), (75, -20.0), (78, -20.0), (81, -20.0), (85, -20.0), (89, -20.0)],
        )

    def test_woailuo_helper_timeline_keeps_source_display_list(self):
        timeline = json.loads(
            (ROOT / "data/slices/woailuo-helper.timeline.json").read_text(encoding="utf-8")
        )
        self.assertEqual(timeline["timeline"], "root")
        self.assertEqual(timeline["frame_count"], 85)
        self.assertEqual(timeline["source_swf"]["path"], "game/fighter/fz/woailuo.swf")
        self.assertEqual(timeline["frames"][0]["display_list"], [])
        self.assertTrue(timeline["frames"][1]["display_list"])
        atm_frames = [
            frame["frame"]
            for frame in timeline["frames"]
            if any(item.get("name") == "atm1" for item in frame["display_list"])
        ]
        self.assertEqual(atm_frames[0], 44)
        self.assertEqual(atm_frames[-1], 85)


class CameraSourceTests(unittest.TestCase):
    def test_fight_camera_constants_match_main_swf(self):
        scripts = json.loads((ROOT / "scripts/main.json").read_text(encoding="utf-8"))[
            "scripts"
        ]
        by_path = {item["path"]: item["source"] for item in scripts}
        camera = by_path["DefineSprite_1991/frame_1/DoAction.as"]
        globals_src = by_path["frame_7/DoAction.as"]
        self.assertIn("var _tweenX = 0.5;", camera)
        self.assertIn("var _scaleMin = 0.8;", camera)
        self.assertIn("var _jlMax = 700;", camera)
        self.assertIn("_loc19_ = 1000;", camera)
        self.assertIn("_loc6_ = 2 * (_loc18_ / _loc19_);", camera)
        self.assertIn("var _loc7_ = 300 - _loc15_ * _loc6_;", camera)
        self.assertIn("var _loc21_ = 620 - _loc24_ * _loc6_;", camera)
        self.assertIn("var _loc20_ = 400;", camera)
        self.assertIn("var _loc4_ = 20;", camera)
        self.assertIn("var _loc5_ = _root.mapSizeX - 30;", camera)
        self.assertIn("_root.game._xscale += (_loc6_ * 100 - _root.game._xscale) * _tweenX;", camera)
        self.assertIn("var mapSizeX = 1000;", globals_src)
        self.assertIn("var floorY = -25;", globals_src)
        self.assertIn("var p1ox = 320;", globals_src)
        self.assertIn("var p2ox = 650;", globals_src)

    def test_all_focus_scale_follows_source_formula(self):
        def scale(distance):
            remain = 1000 - distance
            value = 0.5 if remain <= 0 else 2 * (remain / 1000)
            return max(value, 0.8)

        self.assertAlmostEqual(scale(0), 2.0)
        self.assertAlmostEqual(scale(500), 1.0)
        self.assertAlmostEqual(scale(600), 0.8)
        self.assertAlmostEqual(scale(700), 0.8)
        self.assertAlmostEqual(scale(1000), 0.8)


if __name__ == "__main__":
    unittest.main()
