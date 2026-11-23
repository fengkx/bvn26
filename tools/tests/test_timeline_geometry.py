import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
import extract_timeline_geometry as timeline_geometry


class TimelineGeometryTests(unittest.TestCase):
    def test_linear_gradient_keeps_contour_matrix_and_alpha_stops(self):
        shape = ET.fromstring("""<item><shapes><fillStyles><fillStyles>
          <item fillStyleType="16"><gradientMatrix scaleX="0.0" scaleY="0.0"
            rotateSkew0="0.25" rotateSkew1="-0.25"/>
            <gradient spreadMode="0" interpolationMode="0"><gradientRecords>
              <item ratio="0"><color red="0" green="0" blue="0" alpha="255"/></item>
              <item ratio="122"><color red="0" green="0" blue="0" alpha="0"/></item>
              <item ratio="255"><color red="0" green="0" blue="0" alpha="255"/></item>
            </gradientRecords></gradient></item></fillStyles></fillStyles>
          <shapeRecords><item type="StyleChangeRecord" stateFillStyle1="true" fillStyle1="1"
            stateMoveTo="true" moveDeltaX="0" moveDeltaY="0"/>
            <item type="StraightEdgeRecord" deltaX="40"/><item type="StraightEdgeRecord" deltaY="20"/>
            <item type="StraightEdgeRecord" deltaX="-40"/><item type="StraightEdgeRecord" deltaY="-20"/>
            <item type="EndShapeRecord"/></shapeRecords></shapes></item>""")
        fill = timeline_geometry.single_linear_gradient(shape)
        self.assertEqual(len(fill['polygon']), 4)
        self.assertEqual(fill['matrix']['rotateSkew0'], 0.25)
        self.assertEqual([(s['ratio'], s['rgba'][3]) for s in fill['stops']],
                         [(0, 255), (122, 0), (255, 255)])

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
                    "display_list_frame_events": [[]],
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


if __name__ == "__main__":
    unittest.main()
