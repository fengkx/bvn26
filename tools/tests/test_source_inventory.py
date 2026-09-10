import hashlib
import importlib.util
import json
import re
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
hit_receive = load_module(
    "hit_receive", ROOT / "tools/importer/compile_hit_receive.py"
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

    def test_solid_fill_is_compiled_from_fillstyle_type_0(self):
        root = ET.fromstring(
            """<swf _xmlExportMajor="3" _xmlExportMinor="2">
            <tags>
            <item type="DefineShapeTag" shapeId="535">
              <shapeBounds Xmin="0" Ymin="0" Xmax="9540" Ymax="6860"/>
              <shapes>
                <fillStyles>
                  <item type="FILLSTYLE" fillStyleType="0">
                    <color type="RGB" red="0" green="0" blue="0"/>
                  </item>
                </fillStyles>
              </shapes>
            </item>
            <item type="DefineSpriteTag" spriteId="1510" frameCount="1">
              <subTags>
                <item type="PlaceObject2Tag" depth="1" characterId="535" placeFlagMove="false"/>
                <item type="ShowFrameTag"/>
              </subTags>
            </item>
            </tags></swf>"""
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blackmu.xml"
            ET.ElementTree(root).write(path, encoding="unicode")
            result = timeline_geometry.extract_frames(path, 1510)

        shape = next(item for item in result["definitions"] if item["character_id"] == 535)
        self.assertEqual(
            shape["solid_fills"],
            [{"fill_style_type": 0, "red": 0, "green": 0, "blue": 0}],
        )
        self.assertNotIn("bitmap_fills", shape)

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
    def test_summon_guard_is_retained_for_all_source_fighters(self):
        bundles = list((ROOT / "scripts/fighter").glob("*.json"))
        self.assertEqual(len(bundles), 35)
        for path in bundles:
            found = False
            for script in json.loads(path.read_text())["scripts"]:
                function = combat_model.extract_function(script["source"], "doZhaoHuan")
                if function is None:
                    continue
                found = True
                self.assertEqual(combat_model.compile_summon_function(function),
                                 {"skip_if_truthy": "hurtSkling", "set_bs": 1, "energy_delta": -100})
                with self.assertRaises(ValueError):
                    combat_model.compile_summon_function(function.replace("return undefined;", "ql -= 1;"))
            self.assertTrue(found, path)

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
        sbs = [
            item
            for item in naruto["hitbox_windows"]["上必杀"]
            if item["instance_name"] == "sbsatm"
        ]
        sbs2 = [
            item
            for item in naruto["hitbox_windows"]["上必杀"]
            if item["instance_name"] == "sbs2atm"
        ]
        self.assertEqual(sbs[0]["start_frame"], 693)
        self.assertEqual(sbs[0]["end_frame"], 705)
        self.assertEqual(sbs[0]["placed_name"], "fensheng")
        self.assertEqual(sbs[0]["source_path"], "DefineSprite_489/frame_11/DoAction.as")
        self.assertEqual(sbs2[0]["start_frame"], 706)
        self.assertEqual(sbs2[0]["placed_name"], "fensheng")
        self.assertEqual(sbs2[0]["source_path"], "DefineSprite_489/frame_24/DoAction.as")
        placements = [
            item
            for item in naruto["clip_placements"]
            if item["instance_name"] == "fensheng"
        ]
        self.assertEqual(len(placements), 1)
        self.assertEqual(placements[0]["action"], "上必杀")
        self.assertEqual(placements[0]["frame"], 683)
        self.assertEqual(placements[0]["op"], "place_at_opponent")
        self.assertTrue(placements[0]["place_x"])
        self.assertTrue(placements[0]["place_y"])
        self.assertNotIn("y_pixels", placements[0])
        self.assertEqual(
            placements[0]["source_path"],
            "DefineSprite_764/frame_683/DoAction.as",
        )
        self.assertEqual(
            combat_model.parse_place_at_opponent(
                'if(_parent._xscale > 0)\n{\n   fensheng._x = _root.game["p" + pn]._x - _parent._x;\n}\n'
                'else\n{\n   fensheng._x = _parent._x - _root.game["p" + pn]._x;\n}\n'
                'fensheng._y = _root.game["p" + pn]._y - _parent._y;\n'
            ),
            {
                "instance_name": "fensheng",
                "op": "place_at_opponent",
                "place_x": True,
                "place_y": True,
            },
        )
        self.assertIsNone(
            combat_model.parse_place_at_opponent(
                'if(_parent._xscale > 0)\n{\n   if(_parent._x < _root.game["p" + pn]._x)\n'
                '   {\n      zh1atm._x = _root.game["p" + pn]._x - _parent._x;\n   }\n}\n'
            )
        )
        self.assertIsNone(
            combat_model.parse_place_at_opponent(
                '_parent._x = _root.game["p" + pn]._x;\r\n'
            )
        )
        self.assertEqual(
            combat_model.parse_body_warp(
                '_parent._x = _root.game["p" + pn]._x;\r\n'
            ),
            {"op": "warp_to_opponent", "place_x": True},
        )
        self.assertEqual(
            combat_model.parse_body_warp(
                '_parent._x = _root.game["p" + pn]._x;\r\n'
                '_parent._y = _root.game["p" + pn]._y - 40;\r\n'
                "jump = 1;\r\n"
            ),
            {
                "op": "warp_to_opponent",
                "place_x": True,
                "place_y": True,
                "y_pixels": -40.0,
                "set_jump": True,
            },
        )
        self.assertIsNone(
            combat_model.parse_body_warp(
                'if(_parent._xscale > 0)\n{\n   _parent._x = _root.game["p" + pn]._x - 100;\n}\n'
                "else\n{\n   _parent._x = _root.game[\"p\" + pn]._x + 100;\n}\n"
            )
        )
        self.assertEqual(
            combat_model.parse_body_warp(
                'if(_parent._xscale < 0)\r\n{\r\n   _parent._xscale = 100;\r\n'
                '   _parent._x = _root.game["p" + pn]._x - 100;\r\n}\r\nelse\r\n{\r\n'
                '   _parent._xscale = -100;\r\n'
                '   _parent._x = _root.game["p" + pn]._x + 100;\r\n}\r\n'
                '_parent._y = _root.game["p" + pn]._y;\r\n'
            ),
            {
                "op": "warp_to_opponent",
                "place_x": True,
                "xscale_gt_0": {"set_facing": -1, "x_pixels": 100.0},
                "xscale_lt_0": {"set_facing": 1, "x_pixels": -100.0},
                "place_y": True,
            },
        )
        self.assertEqual(
            combat_model.parse_body_warp(
                'if(_parent._xscale > 0)\r\n{\r\n   _parent._xscale = -100;\r\n'
                '   _parent._x = _root.game["p" + pn]._x - '
                '_root.game["p" + pn].mc.bdmn._width * 0.7;\r\n}\r\nelse\r\n{\r\n'
                '   _parent._xscale = 100;\r\n'
                '   _parent._x = _root.game["p" + pn]._x + '
                '_root.game["p" + pn].mc.bdmn._width * 0.7;\r\n}\r\n'
                '_parent._y = _root.game["p" + pn]._y + '
                '_root.game["p" + pn].mc.bdmn._height * 0.5;\r\n'
                "_root.shine();\r\n"
            ),
            {
                "op": "warp_to_opponent",
                "place_x": True,
                "xscale_gt_0": {"set_facing": -1, "x_bdmn_width": -0.7},
                "xscale_lt_0": {"set_facing": 1, "x_bdmn_width": 0.7},
                "place_y": True,
                "y_bdmn_height": 0.5,
            },
        )
        self.assertEqual(
            combat_model.parse_body_warp(
                'if(_parent._xscale > 0)\r\n{\r\n   _parent._xscale = 100;\r\n'
                '   _parent._x = _root.game["p" + pn]._x - '
                '_root.game["p" + pn].mc.bdmn._width;\r\n}\r\nelse\r\n{\r\n'
                '   _parent._xscale = -100;\r\n'
                '   _parent._x = _root.game["p" + pn]._x + '
                '_root.game["p" + pn].mc.bdmn._width;\r\n}\r\n'
            ),
            {
                "op": "warp_to_opponent",
                "place_x": True,
                "xscale_gt_0": {"set_facing": 1, "x_bdmn_width": -1.0},
                "xscale_lt_0": {"set_facing": -1, "x_bdmn_width": 1.0},
            },
        )
        self.assertEqual(ichigo["body_warps"], [])
        warps = [
            item
            for item in naruto["body_warps"]
            if item["action"] == "超必杀"
        ]
        self.assertEqual([item["frame"] for item in warps], [832, 884])
        self.assertEqual(warps[0]["op"], "warp_to_opponent")
        self.assertTrue(warps[0]["place_x"])
        self.assertNotIn("place_y", warps[0])
        self.assertEqual(
            warps[0]["source_path"],
            "DefineSprite_764/frame_832/DoAction.as",
        )
        self.assertTrue(warps[1]["place_y"])
        self.assertEqual(warps[1]["y_pixels"], -40.0)
        self.assertTrue(warps[1]["set_jump"])
        self.assertEqual(
            warps[1]["source_path"],
            "DefineSprite_764/frame_884/DoAction.as",
        )
        rasengan_exit = naruto["action_exits"]["螺旋手里剑1"]
        self.assertEqual(rasengan_exit["frame"], 902)
        self.assertEqual(rasengan_exit["target"], "螺旋手里剑1")
        self.assertEqual(
            rasengan_exit["source_path"],
            "DefineSprite_764/frame_902/DoAction.as",
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
        self.assertNotIn("防御2", naruto["action_exits"])
        self.assertNotIn("防御2", ichigo["action_exits"])
        # Unconditional gotoAndStop before end_frame, including 击飞.
        self.assertEqual(naruto["action_exits"]["砍技2"]["frame"], 364)
        self.assertEqual(naruto["action_exits"]["招1"]["frame"], 408)
        self.assertEqual(naruto["action_exits"]["招2"]["frame"], 458)
        self.assertEqual(naruto["action_exits"]["上必杀"]["frame"], 735)
        self.assertEqual(naruto["action_exits"]["招换"]["frame"], 981)
        self.assertEqual(naruto["action_exits"]["落地"]["frame"], 119)
        self.assertEqual(naruto["action_exits"]["落地"]["target"], "站立")
        self.assertEqual(naruto["action_exits"]["跳招3"]["frame"], 168)
        self.assertEqual(naruto["action_exits"]["防住"]["frame"], 1011)
        self.assertEqual(naruto["action_exits"]["击落地"]["frame"], 1069)
        self.assertEqual(naruto["action_exits"]["起身"]["frame"], 1087)
        self.assertEqual(naruto["action_exits"]["超必杀2"]["frame"], 942)
        self.assertEqual(naruto["action_exits"]["超必杀2"]["target"], "击飞")
        self.assertEqual(naruto["action_exits"]["超必杀2"]["source_path"], "DefineSprite_764/frame_942/DoAction.as")
        # Same frame: yup=5; htx=15; jhp=0; zl=0; gotoAndStop("击飞"); play();
        self.assertEqual(naruto["action_exits"]["超必杀2"]["yup"], 5)
        self.assertEqual(naruto["action_exits"]["超必杀2"]["htx"], 15)
        self.assertEqual(naruto["action_exits"]["超必杀2"]["jhp"], 0)
        self.assertEqual(naruto["hurt"]["launch_stop_frame"], 1035)
        self.assertEqual(ichigo["hurt"]["launch_stop_frame"], 759)
        # 一护 砍技1 has no 砍技12 fallthrough; frame 278 leaves to 站立.
        self.assertEqual(ichigo["action_exits"]["砍技1"]["frame"], 278)
        self.assertEqual(ichigo["action_exits"]["砍技1"]["target"], "站立")
        self.assertFalse(
            any(item["from"] == "砍技1" for item in ichigo["timeline_fallthroughs"])
        )
        self.assertEqual(ichigo["action_exits"]["砍技2"]["frame"], 312)
        self.assertEqual(ichigo["action_exits"]["招1"]["frame"], 350)
        self.assertEqual(ichigo["action_exits"]["招3"]["frame"], 437)
        self.assertEqual(ichigo["action_exits"]["上必杀"]["frame"], 572)
        self.assertEqual(ichigo["action_exits"]["超必杀"]["frame"], 639)
        self.assertEqual(ichigo["action_exits"]["招换"]["frame"], 682)
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
        self.assertEqual(by_label["砍4"]["implementation"], "wired")
        self.assertFalse(any(gap["label"] == "万解" for gap in catalog["gaps"] if gap["kind"] == "command"))
        self.assertFalse(
            any(
                gap["from"] == "砍3" and gap["to"] == "砍4"
                for gap in catalog["gaps"]
                if gap["kind"] == "cancel"
            )
        )
        # Source order only: magichit1 is after skill1, bisha after bishaUP.
        # Stand runtime takes the earlier leaving goto; these indices stay later.
        self.assertGreater(
            by_label["招1"]["dispatch_orders"]["stand"],
            by_label["砍技1"]["dispatch_orders"]["stand"],
        )
        self.assertGreater(
            by_label["必杀"]["dispatch_orders"]["stand"],
            by_label["上必杀"]["dispatch_orders"]["stand"],
        )
        cancels = catalog["cancel_windows"]
        slash4 = next(
            item
            for item in cancels
            if item["from"] == "砍3" and item["to"] == "砍4"
        )
        self.assertEqual(slash4["predicate"], "nornalhit")
        self.assertTrue(slash4["combo"])
        self.assertEqual(slash4["start_frame"], 217)
        self.assertGreaterEqual(slash4["end_frame"], 217)
        self.assertEqual(slash4["implementation"], "wired")
        self.assertTrue(
            any(
                item["from"] == "落地" and item["to"] == "砍1" and item["implementation"] == "wired"
                for item in cancels
            )
        )
        self.assertTrue(
            any(
                item["from"] == "击落地"
                and item["to"] == "起身"
                and item["implementation"] == "wired"
                for item in cancels
            )
        )
        self.assertTrue(
            any(
                item["from"] == "瞬步"
                and item["to"] == "必杀"
                and item["implementation"] == "wired"
                for item in cancels
            )
        )
        ichigo_cancels = ichigo["command_catalog"]["cancel_windows"]
        self.assertTrue(
            any(
                item["from"] == "砍1" and item["to"] == "万解" and item["implementation"] == "wired"
                for item in ichigo_cancels
            )
        )
        self.assertTrue(
            any(
                item["from"] == "招21" and item["implementation"] == "wired"
                for item in ichigo_cancels
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
        dash = next(
            window for window in naruto["motion_windows"] if window["action"] == "瞬步"
        )
        self.assertEqual(dash["forward_speed_factor"], 2.5)
        self.assertEqual(dash["start_frame"], 21)
        jump_slash = next(
            window for window in naruto["motion_windows"] if window["action"] == "跳砍"
        )
        self.assertEqual(jump_slash["steer_speed_factor"], 1.0)
        self.assertNotIn("vertical_pixels", jump_slash)
        ichigo_jump_slash = next(
            window for window in ichigo["motion_windows"] if window["action"] == "跳砍"
        )
        self.assertEqual(ichigo_jump_slash["steer_speed_factor"], 1.0)
        self.assertEqual(ichigo_jump_slash["vertical_pixels"], -1.0)
        ichigo_air_ranged = next(
            window for window in ichigo["motion_windows"] if window["action"] == "跳招"
        )
        self.assertEqual(ichigo_air_ranged["forward_pixels"], -1.0)
        self.assertEqual(ichigo_air_ranged["vertical_pixels"], -1.0)
        ichigo_dash = next(
            window for window in ichigo["motion_windows"] if window["action"] == "瞬步"
        )
        self.assertEqual(ichigo_dash["forward_speed_factor"], 2.5)
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
        self.assertEqual(ichigo["summon_events"][0]["set_bs"], 1)
        self.assertEqual(ichigo["summon_events"][0]["skip_if_truthy"], "hurtSkling")
        self.assertTrue(naruto["is_naruto"])
        self.assertFalse(ichigo["is_naruto"])
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
        self.assertEqual(gaara["hide_frames"], [])
        self.assertEqual(gaara["attacks"]["atm1"]["damage"], 30)
        self.assertEqual(gaara["attacks"]["atm1"]["hitstun_ms"], 500)
        self.assertEqual(gaara["attacks"]["atm1"]["reaction_label"], "被打")
        self.assertEqual(kon["end_frame"], 102)
        self.assertEqual(kon["hide_frames"], [])
        self.assertEqual(kon["clip_load_events"], [])
        self.assertEqual(gaara["clip_load_events"][0]["frame"], 44)
        self.assertEqual(gaara["clip_load_events"][0]["depth"], 2)
        self.assertEqual([(e["frame"], e["helper"]) for e in kon["presentation_events"] if e["op"].startswith("super_")], [(15, True), (30, False)])
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


class HitReceiveChainTests(unittest.TestCase):
    """SOP step A: 35 playable fighters share the hit-receive functions."""

    def test_playable_fighters_share_hit_receive_functions(self):
        playable = hit_receive.playable_fighter_paths(ROOT)
        self.assertEqual(len(playable), 35)
        reference = hit_receive.load_bundle(ROOT / "scripts/fighter/minren.json")
        ref_blob = hit_receive.bundle_blob(reference)
        expected = {
            name: hit_receive.function_hash(ref_blob, name)
            for name in hit_receive.HIT_RECEIVE_FUNCS
        }
        ref_defence = hit_receive.on_defence_hit_receive(ref_blob)
        self.assertIsNotNone(ref_defence)
        defence_hash = hashlib.sha256(
            hit_receive.normalize_source(ref_defence).encode("utf-8")
        ).hexdigest()
        on_be_hit = hit_receive.extract_function(ref_blob, "onBeHit")
        self.assertIn("hits++", on_be_hit)
        self.assertIn("hits>1", re.sub(r"\s+", "", on_be_hit))
        self.assertIn('gotoAndPlay("连击")', on_be_hit)

        for path in playable:
            bundle = hit_receive.load_bundle(path)
            blob = hit_receive.bundle_blob(bundle)
            for name, digest in expected.items():
                self.assertEqual(
                    hit_receive.function_hash(blob, name),
                    digest,
                    f"{path.name} {name} diverged",
                )
            defence = hit_receive.on_defence_hit_receive(blob)
            self.assertIsNotNone(defence, path.name)
            self.assertEqual(
                hashlib.sha256(
                    hit_receive.normalize_source(defence).encode("utf-8")
                ).hexdigest(),
                defence_hash,
                f"{path.name} onDefence(bdfyxg) diverged",
            )
            self.assertTrue(
                any("hits++" in script["source"] for script in bundle["scripts"]),
                path.name,
            )
            self.assertTrue(
                hit_receive.compile_hits_reset_frames(bundle),
                f"{path.name} missing hits = 0;",
            )
            self.assertTrue(
                hit_receive.compile_show_face_labels(bundle),
                f"{path.name} missing showFace label",
            )

    def test_helpers_have_no_hit_receive_chain(self):
        helpers = hit_receive.helper_fighter_paths(ROOT)
        self.assertEqual(len(helpers), 26)
        for path in helpers:
            bundle = hit_receive.load_bundle(path)
            blob = hit_receive.bundle_blob(bundle)
            for name in hit_receive.HIT_RECEIVE_FUNCS:
                self.assertIsNone(hit_receive.function_hash(blob, name), path.name)
            self.assertFalse(
                any("hits++" in script["source"] for script in bundle["scripts"]),
                path.name,
            )
            self.assertIsNone(hit_receive.on_defence_hit_receive(blob), path.name)

    def test_compiled_hit_receive_follows_source(self):
        naruto = combat_model.build_model(
            ROOT / "data/slices/minren-base.json",
            ROOT / "data/slices/minren-base.timeline.json",
            ROOT / "scripts/fighter/minren.json",
        )
        self.assertIn("1", naruto["attacks_by_form"])
        self.assertGreaterEqual(len(naruto["attacks_by_form"]), 1)
        self.assertEqual(naruto["attacks_by_form"]["1"]["attacks"]["kj1"]["impact_strength"], 15)
        self.assertTrue(
            any(item["frame"] == 2 for item in naruto["hits_reset_frames"])
        )
        self.assertTrue(naruto["on_be_hit_frames"])
        self.assertIn("鸣人2", naruto["face_labels"])
        starts = [item for item in naruto["super_events"] if item.get("op") == "super_start"]
        self.assertTrue(starts)
        self.assertTrue(any(item.get("face_label") == "鸣人2" for item in naruto["super_events"]))
        self.assertFalse(
            any(item.get("action") == "站立" for item in naruto["super_events"]),
            "frame 1 init must not compile function-body bsw mentions",
        )

        main_bundle = hit_receive.load_bundle(ROOT / "scripts/main.json")
        shared = hit_receive.compile_shared_hit_receive(
            main_bundle, swf_path=ROOT / "game/main.swf"
        )
        self.assertEqual(shared["combo_hud"]["p1hits_pn"], 2)
        self.assertEqual(shared["combo_hud"]["p2hits_pn"], 1)
        self.assertEqual(shared["combo_hud"]["show_number_frame"], 11)
        self.assertEqual(shared["combo_hud"]["reset_frame"], 50)
        self.assertEqual(naruto["combo_hud"]["play_frame"], 10)
        self.assertEqual(shared["hit_fx"]["bdxg"][3], "XG_qdjx")
        self.assertEqual(shared["hit_fx"]["bdxg"][5], "XG_mfdjx")
        self.assertEqual(shared["hit_fx"]["bdfyxg"][2], "XG_fyq")
        self.assertEqual(shared["hit_fx"]["bdfyxg"][5], "XG_mffyx")
        self.assertEqual(shared["hit_fx"]["clips"]["XG_bs"]["source_prefix"], "DefineSprite_459_XG_bs")
        self.assertEqual(shared["hit_fx"]["clips"]["XG_cbs"]["source_prefix"], "DefineSprite_441_XG_cbs")
        super_pres = shared["super_presentation"]
        self.assertEqual(super_pres["black_mu"]["sprite_id"], 1510)
        self.assertEqual(super_pres["black_mu"]["super_frame"], 2)
        self.assertEqual(super_pres["black_mu"]["idle_frame"], 1)
        self.assertTrue(super_pres["black_mu_imported"])
        self.assertTrue(super_pres["ts_face_imported"])
        self.assertTrue(super_pres["xg_imported"])
        self.assertTrue(super_pres["black_mu"]["imported"])
        self.assertTrue(super_pres["ts_face"]["imported"])
        self.assertEqual(super_pres["black_mu"]["directory"], "res://generated/main/blackMu")
        self.assertEqual(super_pres["ts_face"]["pn_face_slot"]["2"], "face_p1")
        self.assertEqual(super_pres["ts_face"]["pn_face_slot"]["1"], "face_p2")
        self.assertEqual(super_pres["ts_face"]["in_frame"], 5)
        self.assertEqual(super_pres["ts_face"]["portrait_labels"]["鸣人2"], 23)
        self.assertEqual(super_pres["xg"]["bsd"], "XG_bs")
        self.assertEqual(super_pres["xg"]["cbsd"], "XG_cbs")
        self.assertEqual(super_pres["hide_stage_instances"], ["bgmc", "fgmc"])
        bsd = next(item for item in naruto["super_events"] if item.get("frame") == 507)
        self.assertEqual(bsd["xg"], "XG_bs")
        cbsd = next(item for item in naruto["super_events"] if item.get("frame") == 752)
        self.assertEqual(cbsd["xg"], "XG_cbs")
        self.assertEqual(cbsd["kind"], "cbsd")
        self.assertEqual(shared["hit_fx"]["bdfyxg"][1], "XG_fykan")
        fykan = shared["hit_fx"]["clips"]["XG_fykan"]["presentation_events"]
        self.assertTrue(any(item["op"] == "unload" and item["frame"] == 11 for item in fykan))

    def test_hit_effect_clips_keep_source_start_sound(self):
        # main.swf ExportAssets: each XG clip is its own DefineSprite and
        # starts one library sound on its frame 1. bdfyxg/bdfyxg2 pick the
        # guard clips, bdxg the hit clips.
        expected = {
            "XG_kan": (159, 128),
            "XG_kanx": (125, 114),
            "XG_qdj": (256, 239),
            "XG_qdjx": (236, 219),
            "XG_mfdj": (314, 301),
            "XG_mfdjx": (298, 219),
            "XG_fykan": (216, 215),
            "XG_fykanx": (214, 203),
            "XG_fyq": (200, 197),
            "XG_fyqx": (196, 179),
            "XG_mffy": (280, 197),
            "XG_mffyx": (279, 179),
            "XG_bs": (459, 444),
            "XG_cbs": (441, 426),
        }
        main_bundle = hit_receive.load_bundle(ROOT / "scripts/main.json")
        shared = hit_receive.compile_shared_hit_receive(main_bundle)
        compiled = set(shared["hit_fx"]["bdfyxg"].values()) | set(
            shared["hit_fx"]["bdfyxg2"].values()
        )
        self.assertTrue(compiled <= set(expected), compiled - set(expected))
        for clip, (sprite_id, sound_id) in expected.items():
            directory = ROOT / "godot/generated/effects" / clip
            timeline = json.loads((directory / "timeline.json").read_text(encoding="utf-8"))
            self.assertEqual(timeline["sprite_id"], sprite_id, clip)
            events = [
                event
                for event in timeline["frames"][0]["events"]
                if event["type"] == "start_sound"
            ]
            self.assertEqual([event["sound_id"] for event in events], [sound_id], clip)
            assets = json.loads((directory / "assets.json").read_text(encoding="utf-8"))
            materialized = {
                asset["character_id"]: asset["path"] for asset in assets["assets"]
            }
            self.assertEqual(materialized.get(sound_id), f"{sound_id}.mp3", clip)
            self.assertTrue((directory / f"{sound_id}.mp3").is_file(), clip)

    def test_start_sound_keeps_source_envelope(self):
        # XG_fyq / XG_mffy share soundId 197 and carry one SOUNDINFO record,
        # so the blocked light hit is quieter than XG_fykan's unscaled sound.
        for clip in ("XG_fyq", "XG_mffy"):
            timeline = json.loads(
                (ROOT / "godot/generated/effects" / clip / "timeline.json").read_text(
                    encoding="utf-8"
                )
            )
            event = next(
                item
                for item in timeline["frames"][0]["events"]
                if item["type"] == "start_sound"
            )
            self.assertEqual(
                event["envelope"],
                [{"pos44": 0, "left_level": 18008, "right_level": 18893}],
                clip,
            )
        plain = json.loads(
            (ROOT / "godot/generated/effects/XG_fykan/timeline.json").read_text(
                encoding="utf-8"
            )
        )
        event = next(
            item for item in plain["frames"][0]["events"] if item["type"] == "start_sound"
        )
        self.assertNotIn("envelope", event)


if __name__ == "__main__":
    unittest.main()
