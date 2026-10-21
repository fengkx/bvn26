"""Source evidence for generic nested visual controls and blend inheritance."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "importer"))
from extract_timeline_geometry import build_frames, visual_control_actions


class VisualTimelineControlsTest(unittest.TestCase):
    def test_static_controls(self):
        self.assertEqual(visual_control_actions("0700"), [{"op": "stop"}])
        self.assertEqual(visual_control_actions("81020004000600"),
                         [{"op": "goto", "frame": 5}, {"op": "play"}])
        self.assertEqual(visual_control_actions("8c0400656e64000700"),
                         [{"op": "goto", "label": "end"}, {"op": "stop"}])

    def test_conditional_or_expression_block_is_not_unconditional(self):
        self.assertEqual(visual_control_actions("96020005010700"), [])
        self.assertEqual(visual_control_actions("9d020001000700"), [])

    def test_move_retains_blend_and_new_placement_resets_it(self):
        tags = ET.fromstring('''<tags>
          <item type="PlaceObject3Tag" depth="2" characterId="7" blendMode="4"/>
          <item type="ShowFrameTag"/>
          <item type="PlaceObject3Tag" depth="2" placeFlagMove="true"><matrix translateX="20"/></item>
          <item type="ShowFrameTag"/>
          <item type="PlaceObject3Tag" depth="2" characterId="8"/>
          <item type="ShowFrameTag"/>
        </tags>''')
        frames = build_frames(list(tags))
        self.assertEqual(frames[1]["display_list"][0]["blend_mode"], 4)
        self.assertNotIn("blend_mode", frames[2]["display_list"][0])


if __name__ == "__main__":
    unittest.main()
