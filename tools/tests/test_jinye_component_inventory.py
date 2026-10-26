import unittest
import xml.etree.ElementTree as ET

from tools.probes.inventory_jinye_component import timeline


class JinyeComponentInventoryTests(unittest.TestCase):
    def fixture(self):
        sprite = ET.Element("item", {"frameCount": "21"})
        tags = ET.SubElement(sprite, "subTags")
        for frame in range(1, 22):
            if frame == 21:
                ET.SubElement(tags, "item", {"type": "RemoveObject2Tag", "depth": "1"})
            else:
                attributes = {"type": "PlaceObject2Tag", "depth": "1",
                              "placeFlagHasMatrix": "true",
                              "placeFlagHasCharacter": "true" if frame in (1, 10, 20) else "false",
                              "placeFlagMove": "false" if frame == 1 else "true"}
                if frame in (1, 10, 20):
                    attributes["characterId"] = "57" if frame == 10 else "56"
                tag = ET.SubElement(tags, "item", attributes)
                ET.SubElement(tag, "matrix", {"translateX": str(frame)})
            ET.SubElement(tags, "item", {"type": "ShowFrameTag"})
        return sprite

    def test_replacements_and_removal_are_retained(self):
        result = timeline(self.fixture())
        self.assertEqual([row["placements"][0]["character_id"] for row in result["frames"][:20]],
                         [56] * 9 + [57] * 10 + [56])
        self.assertEqual(result["frames"][-1]["placements"], [])
        self.assertEqual([(row["frame"], row["operation"]) for row in result["events"]
                          if row["operation"] != "move"],
                         [(1, "place"), (10, "replace"), (20, "replace"), (21, "remove")])

    def test_unhandled_clip_action_fails_with_source_location(self):
        sprite = self.fixture()
        sprite.find("subTags/item").set("placeFlagHasClipActions", "true")
        with self.assertRaisesRegex(ValueError, "DefineSprite_58/frame_1/depth_1: unhandled placement flag"):
            timeline(sprite)

    def test_absent_move_and_unknown_tag_fail(self):
        sprite = self.fixture()
        sprite.find("subTags/item").set("placeFlagMove", "true")
        with self.assertRaisesRegex(ValueError, "inconsistent lifetime"):
            timeline(sprite)
        sprite = self.fixture()
        sprite.find("subTags/item").set("type", "DoActionTag")
        with self.assertRaisesRegex(ValueError, "DefineSprite_58/frame_1: unhandled tag DoActionTag"):
            timeline(sprite)


if __name__ == "__main__":
    unittest.main()
