import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import split_web_packs as packs


class PackFamilies(unittest.TestCase):
    def test_publishes_standalone_recovery_assets_with_the_roster_labels(self):
        project = Path(__file__).resolve().parents[2] / "godot"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            packs.publish_diagnostics(project, output)
            script = (output / "crash_archive.js").read_text()
            names = json.loads(script.split("const names = ", 1)[1].split(";", 1)[0])
            self.assertEqual(names["res://generated/helpers/jinye"], "山中井野")
            self.assertEqual(names["res://generated/helpers/stake"], "柯雅泰·史塔克")
            self.assertIn("res://generated/forms/yihu-3", names)
            page = (output / "diagnostics.html").read_text()
            self.assertIn('src="crash_archive.js"', page)
            self.assertNotIn("$GODOT", page)

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
