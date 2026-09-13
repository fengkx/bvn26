"""Helper probes use the source catalog instead of an incomplete helper list."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/probes"))
from build_ai_reference import helper_observer_source, resolve_helper_selection


class HelperSourceResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "manifest.json").read_text())["fighter_catalog"]

    def test_existing_helper_aliases_resolve_by_source_filename(self):
        expected = {"kon": "魂", "woailuo": "我爱罗", "you": "鼬"}
        for source_stem, character_id in expected.items():
            with self.subTest(source_stem=source_stem):
                selection = resolve_helper_selection(self.catalog, source_stem)
                self.assertEqual(selection["character_id"], character_id)
                self.assertEqual(selection["asset"], source_stem)

    def test_ino_resolves_from_manifest_fzurl(self):
        by_id = resolve_helper_selection(self.catalog, "松本")
        by_source = resolve_helper_selection(self.catalog, "jinye")
        self.assertEqual(by_id, by_source)
        self.assertEqual(by_id, {
            "character_id": "松本", "asset": "jinye", "url": "jinye.swf",
        })

    def test_helper_observer_handles_missing_and_source_named_clips(self):
        source = helper_observer_source(["atm1"])
        self.assertIn("var clip = helper[instanceName]", source)
        self.assertIn('aiHelperClipFrame(f,"atm2")', source)
        self.assertIn('"atm1" + "=" + _root.aiHelperClipFrame(f,"atm1")', source)
        self.assertNotIn('f.atm2._currentframe', source)


if __name__ == "__main__":
    unittest.main()
