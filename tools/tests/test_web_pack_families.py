import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import split_web_packs as packs


class PackFamilies(unittest.TestCase):
    def test_new_form_must_travel_with_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            for fighter in packs.BOOT_FIGHTERS:
                (project / "generated/fighters" / fighter).mkdir(parents=True)
            (project / "generated/fighters/second").mkdir(parents=True)
            base = project / "generated/fighters/fighter"
            base.mkdir(parents=True)
            form = project / "generated/forms/fighter-4"
            form.mkdir(parents=True)
            (form / "timeline.json").touch()
            with self.assertRaisesRegex(ValueError, "Undeclared form"):
                packs.family_directories(project)
            (base / "form_profiles.json").write_text(json.dumps({
                "profiles": {"4": {"directory": "res://generated/forms/fighter-4"}}
            }))
            self.assertEqual(packs.family_directories(project), {
                "fighters/fighter": "fighter", "forms/fighter-4": "fighter",
                "fighters/second": "second"
            })
            (form / "timeline.json").unlink()
            with self.assertRaisesRegex(ValueError, "Missing form"):
                packs.family_directories(project)
