import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web_import_cache import import_stem, restore, store


class WebImportCacheTests(unittest.TestCase):
    def test_warm_restore_respects_sources_settings_and_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "cache"

            def stage(name):
                project = root / name
                project.mkdir()
                (project / "project.godot").write_text("config_version=5")
                for folder in ("title", "fight"):
                    (project / folder).mkdir()
                    (project / folder / "sprite.png").write_bytes(b"original")
                return project

            cold = stage("cold")
            plan = restore(cold, cache, "engine-1")
            self.assertEqual(len(plan), 2)
            for folder, names, _, _ in plan:
                for name in names:
                    source = Path(folder) / name
                    (cold / source.with_suffix(".png.import")).write_bytes(b"settings")
                    for ext in (".ctex", ".md5"):
                        (cold / ".godot/imported" / (import_stem(source) + ext)).write_bytes(b"result")
            store(cold, cache, plan)
            warm = stage("warm")
            self.assertEqual(restore(warm, cache, "engine-1"), [])
            self.assertEqual((warm / "fight/sprite.png.import").read_bytes(), b"settings")
            changed = stage("changed")
            (changed / "title/sprite.png").write_bytes(b"changed")
            self.assertEqual([row[0] for row in restore(changed, cache, "engine-1")], ["title"])
            self.assertFalse((changed / "title/sprite.png.import").exists())
            custom = stage("custom")
            settings = custom / "title/sprite.png.import"
            settings.write_bytes(b"custom")
            self.assertEqual(restore(custom, cache, "engine-1"), [])
            self.assertEqual(settings.read_bytes(), b"custom")
            self.assertEqual(len(restore(stage("upgrade"), cache, "engine-2")), 2)
            for archive in cache.glob("*.zip"):
                archive.write_bytes(b"incomplete")
            self.assertEqual(len(restore(stage("damaged"), cache, "engine-1")), 2)


if __name__ == "__main__":
    unittest.main()
