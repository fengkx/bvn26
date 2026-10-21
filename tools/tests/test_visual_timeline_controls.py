"""Source evidence for generic nested visual controls and blend inheritance."""
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "importer"))
from extract_timeline_geometry import build_frames, visual_control_actions


class VisualTimelineControlsTest(unittest.TestCase):
    def test_static_controls(self):
        self.assertEqual(visual_control_actions("0700"), [{"op": "stop"}])
        self.assertEqual(visual_control_actions("81020004000600"),
                         [{"op": "goto", "frame": 5}, {"op": "play"}])
        self.assertEqual(visual_control_actions("8c0400656e64000700"),
                         [{"op": "goto", "label": "end"}, {"op": "stop"}])

    def test_stack_values_do_not_make_a_stop_conditional(self):
        self.assertEqual(visual_control_actions("96020005010700"), [{"op": "stop"}])
        self.assertEqual(visual_control_actions("9d020001000700"), [])
        self.assertEqual(visual_control_actions("07003d00"), [{"op": "stop"}])
        self.assertEqual(visual_control_actions("073d00"), [])
        # stop(); var speed = 25; must stop on the first frame, before init.
        self.assertEqual(visual_control_actions("07960c000073706565640007190000003c00"), [{"op": "stop"}])

    def test_unsupported_blend_fails_at_import_and_build(self):
        from visual_blend_modes import validate_timeline_blends
        for mode in [7, 10, 11, 12, 13, 99]:
            tag = ET.fromstring(f'<item type="PlaceObject3Tag" depth="1" characterId="7" blendMode="{mode}"/>')
            with self.assertRaisesRegex(ValueError, "Unsupported Flash blend mode"):
                build_frames([tag])
            with self.assertRaisesRegex(ValueError, "Unsupported Flash blend mode"):
                validate_timeline_blends({"definitions": [{"blend_mode": mode}]}, "fixture")

    def test_manifest_generation_checks_nested_timeline_modes(self):
        import build_online_manifest
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timeline = root / "godot/generated/fighters/fixture/timeline.json"
            timeline.parent.mkdir(parents=True)
            timeline.write_text('{"definitions": [{"blend_mode": 13}]}')
            with patch.object(build_online_manifest, "ROOT", root), \
                    patch.object(build_online_manifest, "GODOT", root / "godot"), \
                    patch.object(build_online_manifest, "relative", side_effect=lambda path: str(path)):
                with self.assertRaisesRegex(ValueError, "Unsupported Flash blend mode 13"):
                    build_online_manifest.make_documents()

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
