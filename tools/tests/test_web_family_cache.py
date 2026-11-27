import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web_family_cache import family_keys, merge_uids, plan, save, uid_rows


class WebFamilyCacheTests(unittest.TestCase):
    def test_keys_follow_family_sources_imports_and_toolchain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "template"
            template.write_bytes(b"engine")
            project = root / "project"
            project.mkdir()
            (project / "project.godot").write_text("[application]")
            preset = project / "export_presets.cfg"
            preset.write_text(f'export_filter="all_resources"\nexclude_filter=""\ncustom_template/release="{template}"\n')
            owners = {"fighters/one": "one", "forms/one-2": "one", "fighters/two": "two"}
            for directory in owners:
                source = project / "generated" / directory
                source.mkdir(parents=True)
                (source / "timeline.json").write_text("{}")
            form = project / "generated/forms/one-2"
            (form / "portrait.png").write_bytes(b"png")
            (form / "portrait.png.import").write_text('importer="texture"\npath="res://.godot/imported/portrait.ctex"\n')
            imported = project / ".godot/imported/portrait.ctex"
            imported.parent.mkdir(parents=True)
            imported.write_bytes(b"native")

            def keys(engine="godot-test"):
                return family_keys(project, owners, engine)

            initial = keys()
            self.assertEqual(set(initial), {"one", "two"})
            (project / "main.gd").write_text("extends Node")
            self.assertEqual(keys(), initial)
            for file in [imported, form / "timeline.json"]:
                original = file.read_bytes()
                file.write_bytes(original + b"changed")
                self.assertNotEqual(keys()["one"], initial["one"])
                self.assertEqual(keys()["two"], initial["two"])
                file.write_bytes(original)
            self.assertNotEqual(keys("new-engine"), initial)
            moved = root / "new-template"
            shutil.copy(template, moved)
            preset.write_text(preset.read_text().replace(str(template), str(moved)))
            self.assertEqual(keys(), initial)
            (form / "controller.gd").write_text("class_name NewClass\nextends Node")
            self.assertNotIn("one", keys())

            cache = root / "cache"
            pack = root / "pack"
            pack.write_bytes(b"native-pack")
            sha = hashlib.sha256(pack.read_bytes()).hexdigest()
            path = b"res://generated/fighters/two/portrait.png"
            row = struct.pack("<QI", 37, len(path)) + path
            save(cache, "two", initial["two"], pack, sha, [row])
            original = preset.read_bytes()
            work = root / "warm"
            plan(project, cache, work, "godot-test", owners)
            hits = json.loads((work / "plan.json").read_text())["hits"]
            self.assertEqual(set(hits), {"two"})
            self.assertIn("res://generated/fighters/two/*", preset.read_text())
            self.assertEqual(list(uid_rows(merge_uids(struct.pack("<I", 0), work, hits))), [(path.decode(), row)])
            preset.write_bytes(original)
            (cache / "two.zip").write_bytes(b"truncated")
            work = root / "damaged"
            plan(project, cache, work, "godot-test", owners)
            self.assertEqual(json.loads((work / "plan.json").read_text())["hits"], {})
            self.assertEqual(preset.read_bytes(), original)

    def test_split_restores_cached_pack_and_its_uid_in_the_core(self):
        from split_web_packs import split

        def pack(path, files):
            data = bytearray(112)
            struct.pack_into("<4sI", data, 0, b"GDPC", 4)
            struct.pack_into("<IQ", data, 20, 2, 112)
            directory = bytearray(struct.pack("<I", len(files)))
            for name, payload in files.items():
                encoded = name.encode()
                encoded += bytes(-len(encoded) % 4)
                directory.extend(struct.pack("<I", len(encoded)) + encoded)
                directory.extend(struct.pack("<QQ", len(data) - 112, len(payload)))
                directory.extend(hashlib.md5(payload).digest() + bytes(4))
                data.extend(payload)
                data.extend(bytes(-len(data) % 16))
            struct.pack_into("<Q", data, 32, len(data))
            path.write_bytes(data + directory)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            source = project / "generated/fighters/rifagu"
            source.mkdir(parents=True)
            (source / "timeline.json").write_text("{}")
            uid = b"res://generated/fighters/rifagu/test.gd"
            row = struct.pack("<QI", 51, len(uid)) + uid
            full = {".godot/uid_cache.bin": struct.pack("<I", 1) + row, "main.gdc": b"core"}
            partial = {".godot/uid_cache.bin": struct.pack("<I", 0), "main.gdc": b"core"}
            full["generated/fighters/rifagu/timeline.json"] = b"{}"
            output, work, cache = root / "output", root / "reuse", root / "cache"
            output.mkdir()
            work.mkdir()
            source_pack = root / "index.pck"
            pack(source_pack, full)
            (work / "plan.json").write_text(json.dumps({"keys": {"rifagu": "v1"}, "hits": {}, "cache": str(cache)}))
            cold = split(source_pack, project, output, work)
            # Reading a warm core produced from the reduced native export must
            # reproduce the full export, including its UID directory entry/hash.
            (work / "rifagu.uids").write_bytes(full[".godot/uid_cache.bin"])
            (output / cold["rifagu"]["file"]).replace(work / cold["rifagu"]["file"])
            (work / "plan.json").write_text(json.dumps({"keys": {"rifagu": "v1"}, "hits": {"rifagu": cold["rifagu"]}, "cache": str(cache)}))
            pack(source_pack, partial)
            self.assertEqual(split(source_pack, project, output, work), cold)
