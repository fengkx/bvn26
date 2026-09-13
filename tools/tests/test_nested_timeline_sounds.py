import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


timeline_geometry = load_module(
    "nested_sound_timeline_geometry",
    ROOT / "tools/importer/extract_timeline_geometry.py",
)
materialize_assets = load_module(
    "nested_sound_materialize_assets",
    ROOT / "tools/importer/materialize_timeline_assets.py",
)


class NestedTimelineSoundTests(unittest.TestCase):
    def test_reachable_child_start_sound_is_preserved_with_its_frame(self):
        xml = """<swf _xmlExportMajor="2" _xmlExportMinor="2">
          <tags>
            <item type="DefineSpriteTag" spriteId="10" frameCount="1">
              <subTags>
                <item type="PlaceObject2Tag" depth="4" characterId="20" placeFlagMove="false" />
                <item type="ShowFrameTag" />
              </subTags>
            </item>
            <item type="DefineSpriteTag" spriteId="20" frameCount="2">
              <subTags>
                <item type="ShowFrameTag" />
                <item type="StartSoundTag" soundId="164">
                  <soundInfo type="SOUNDINFO" hasEnvelope="false" hasInPoint="false"
                    hasLoops="false" hasOutPoint="false" syncStop="false"
                    syncNoMultiple="false" />
                </item>
                <item type="ShowFrameTag" />
              </subTags>
            </item>
            <item type="DefineSoundTag" soundId="164" _externalFile="sounds/164.mp3" />
            <item type="DefineSoundTag" soundId="165" _externalFile="sounds/165.mp3" />
          </tags>
        </swf>"""
        with tempfile.TemporaryDirectory() as directory:
            xml_path = Path(directory) / "source.xml"
            xml_path.write_text(xml)
            result = timeline_geometry.extract_frames(xml_path, 10)

        child = next(item for item in result["definitions"] if item["character_id"] == 20)
        sound = next(item for item in result["definitions"] if item["character_id"] == 164)
        self.assertEqual(child["display_list_frame_events"], [[], [
            {"type": "start_sound", "sound_id": 164}
        ]])
        self.assertEqual(sound["external_file"], "sounds/164.mp3")
        self.assertNotIn(165, {item["character_id"] for item in result["definitions"]})

    def test_materializer_copies_nested_sound_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            (workspace / "sounds").mkdir(parents=True)
            (workspace / "sounds/164.mp3").write_bytes(b"nested sound")
            timeline_path = root / "timeline.json"
            timeline_path.write_text(json.dumps({
                "definitions": [
                    {"character_id": 20, "display_list_frame_events": [
                        [{"type": "start_sound", "sound_id": 164}]
                    ]},
                    {"character_id": 164, "type": "DefineSoundTag",
                     "external_file": "sounds/164.mp3"},
                ],
                "frames": [],
            }))
            output = root / "generated"
            report = materialize_assets.materialize(
                workspace, timeline_path, output
            )

            copied = output / "164.mp3"
            self.assertEqual(copied.read_bytes(), b"nested sound")
            self.assertIn(164, {item["character_id"] for item in report["assets"]})

    def test_sound_asset_inventory_includes_reachable_child_events(self):
        timeline = {
            "frames": [],
            "definitions": [{"display_list_frame_events": [
                [], [{"type": "start_sound", "sound_id": 164}]
            ]}],
        }
        self.assertEqual(materialize_assets._timeline_start_sound_ids(timeline), {164})

    def test_false_soundinfo_flags_are_omitted_and_true_values_preserved(self):
        xml_tag = timeline_geometry.ET.fromstring("""<item type="StartSoundTag" soundId="164">
          <soundInfo type="SOUNDINFO" hasEnvelope="false" hasInPoint="false"
            hasLoops="false" hasOutPoint="false" syncStop="false"
            syncNoMultiple="false" />
        </item>""")
        self.assertEqual(timeline_geometry.sound_info(xml_tag), {})
        xml_tag.find("soundInfo").attrib["syncStop"] = "true"
        xml_tag.find("soundInfo").attrib["hasInPoint"] = "true"
        xml_tag.find("soundInfo").attrib["inPoint"] = "0"
        self.assertEqual(
            timeline_geometry.sound_info(xml_tag),
            {"sync_stop": True, "in_point": 0},
        )


if __name__ == "__main__":
    unittest.main()
