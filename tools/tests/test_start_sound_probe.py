"""Tests for independent source StartSound frame-entry markers."""

from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/probes"))
from instrument_start_sound_tags import (  # noqa: E402
    collect_tags,
    insert_markers,
    marker_script,
    normalize_xml,
    strip_markers,
)


class StartSoundProbeTests(unittest.TestCase):
    def test_independent_markers_cover_multi_action_and_no_action_frames(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            asset = directory / "assets/sounds/17.mp3"
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b"source-mp3")
            xml = directory / "fighter.xml"
            xml.write_text(
                """<swf><tags>
                  <item type="DefineSoundTag" soundId="17" _externalFile="assets/sounds/17.mp3" />
                  <item type="DefineSpriteTag" spriteId="345"><subTags>
                    <item type="DoActionTag" actionBytes="source-a1" />
                    <item type="StartSoundTag" soundId="17"><soundInfo type="SOUNDINFO"
                      syncStop="false" syncNoMultiple="true" hasInPoint="true" inPoint="12" /></item>
                    <item type="DoActionTag" actionBytes="source-a2" />
                    <item type="ShowFrameTag" />
                    <item type="StartSoundTag" soundId="17"><soundInfo type="SOUNDINFO"
                      syncStop="true" syncNoMultiple="false" hasOutPoint="true" outPoint="900" /></item>
                    <item type="StartSoundTag" soundId="17"><soundInfo type="SOUNDINFO"
                      syncStop="false" syncNoMultiple="false" /></item>
                    <item type="DoActionTag" actionBytes="source-a3" />
                    <item type="ShowFrameTag" />
                    <item type="StartSoundTag" soundId="17"><soundInfo type="SOUNDINFO"
                      syncStop="false" syncNoMultiple="false" /></item>
                    <item type="ShowFrameTag" />
                  </subTags></item>
                </tags></swf>"""
            )
            original = ET.parse(xml).getroot()
            tags = collect_tags(xml, directory, 345)
            self.assertEqual([(tag["frame"], tag["sound_id"]) for tag in tags],
                             [(1, 17), (2, 17), (2, 17), (3, 17)])
            self.assertEqual(tags[0]["sound_info"]["attributes"]["inPoint"], "12")
            self.assertEqual(tags[1]["sound_info"]["attributes"]["syncStop"], "true")
            self.assertEqual(tags[0]["asset_sha256"],
                             "31f39946206a0e48ffdd44a8ac15fe2fea15b9b34bce25df78c20f440f7599a3")
            self.assertIn('"case_1|sprite345|1|1|0|17"', marker_script(tags[0], "case_1"))
            unobserved = marker_script(tags[0], "case_1", position_observer_frame=2)
            self.assertNotIn("new Sound(this)", unobserved)
            observed = marker_script(tags[1], "case_1", position_observer_frame=2)
            self.assertIn("new Sound(this)", observed)
            self.assertIn("__aiSoundPositionProbe.position", observed)
            self.assertIn("__aiSoundPositionProbe.duration", observed)
            self.assertNotIn("onSoundComplete", observed)
            self.assertNotIn(".start(", observed)
            self.assertNotIn(".stop(", observed)
            marker_bytes = {
                f"{tag['frame']}:{tag['frame_ordinal']}": f"marker-{index}".encode().hex()
                for index, tag in enumerate(tags)
            }
            insert_markers(original, 345, tags, marker_bytes)
            child_tags = list(original.find("tags")[1].find("subTags"))
            marker_count = 0
            for index, tag in enumerate(child_tags):
                if tag.get("type") != "StartSoundTag":
                    continue
                marker = child_tags[index + 1]
                source_tag = tags[marker_count]
                self.assertEqual(marker.get("type"), "DoActionTag")
                self.assertEqual(marker.get("actionBytes"), marker_bytes[
                    f"{source_tag['frame']}:{source_tag['frame_ordinal']}"])
                marker_count += 1
            self.assertEqual(marker_count, len(tags))

            strip_markers(original, 345, tags, marker_bytes)
            self.assertEqual(normalize_xml(original), normalize_xml(ET.parse(xml).getroot()))
            # Existing frame actions remain in their exact source order and content.
            actions = [tag.get("actionBytes") for tag in original.iter()
                       if tag.get("type") == "DoActionTag"]
            self.assertEqual(actions, ["source-a1", "source-a2", "source-a3"])

    def test_rejects_unhandled_start_sound2(self):
        with tempfile.TemporaryDirectory() as temporary:
            xml = Path(temporary) / "fighter.xml"
            xml.write_text(
                '<swf><tags><item type="DefineSpriteTag" spriteId="345"><subTags>'
                '<item type="StartSound2Tag" soundClassName="voice" />'
                '</subTags></item></tags></swf>'
            )
            with self.assertRaisesRegex(ValueError, "StartSound2Tag"):
                collect_tags(xml, Path(temporary), 345)

    def test_normalization_ignores_only_known_encoding_width_fields(self):
        left = ET.fromstring('<item type="PlaceObjectTag" nScaleBits="1" moveBits="1" depth="2"/>')
        right = ET.fromstring('<item type="PlaceObjectTag" nScaleBits="0" moveBits="0" depth="2"/>')
        self.assertEqual(normalize_xml(left), normalize_xml(right))
        right.set("depth", "3")
        with self.assertRaises(AssertionError):
            self.assertEqual(normalize_xml(left), normalize_xml(right))


if __name__ == "__main__":
    unittest.main()
