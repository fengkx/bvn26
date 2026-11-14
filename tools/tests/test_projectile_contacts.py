"""Projectile callbacks query their own current geometry, not receiver history."""
import json
import re
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
from build_combat_model import parse_projectile_motion, parse_projectile_initialization, parse_clip_timeline
sys.path.insert(0, str(ROOT / "tools/probes"))
from compare_projectile_reference import compare as compare_projectiles


class ProjectileContactTests(unittest.TestCase):
    def test_saved_flash_child_states_reject_post_hit_flight_and_wrong_frame(self):
        base = ROOT / "evidence/combat/projectile-contact-fix/projectile-states"
        for role in ("minren", "rifagu", "yihu"):
            source = base / role / "events.jsonl.gz"
            native = base / role / "native.projectiles.json"
            self.assertEqual(compare_projectiles(source, native)["status"], "matched")
            for field in ("x", "frame", "movspeed"):
                rows = json.loads(native.read_text())
                row = next(row for row in rows if row["played"] == 1)
                row[field] += 1
                with self.subTest(role=role, field=field), tempfile.TemporaryDirectory() as directory:
                    changed = Path(directory) / "native.json"
                    changed.write_text(json.dumps(rows))
                    result = compare_projectiles(source, changed)
                    self.assertEqual(result["status"], "different")
                    self.assertEqual(len(result["differences"]), 1)

    def test_naruto_hitsugaya_contact_locals_and_action_artifacts(self):
        for role, speed_factor in [("minren", 2.0), ("rifagu", 1.0)]:
            combat = json.loads((ROOT / f"godot/generated/fighters/{role}/combat.json").read_text())
            actions = json.loads((ROOT / f"data/actions/{role}-base.json").read_text())
            self.assertEqual(combat["projectiles"], actions["projectiles"])
            self.assertEqual(len(combat["projectiles"]), 1)
            projectile = combat["projectiles"][0]
            self.assertEqual(projectile["initial_variables"], {"played": 0})
            self.assertEqual(projectile["initial_speed_field"], "speed")
            self.assertEqual(projectile["initial_speed_factor"], speed_factor)
            event, = projectile["on_hit_events"]
            self.assertEqual(event["op"], "local_write_group")
            self.assertEqual(event["conditions"], [{"field": "played", "operator": "==", "value": 0}])
            self.assertEqual(event["writes"], [{"field": "played", "value": 1}, {"field": "movspeed", "value": 0}])
            self.assertEqual(event["goto_frame"], 5)
            self.assertTrue(projectile["on_hit_goto_grouped"])
        actions = json.loads((ROOT / "data/actions/Kakashi-base.json").read_text())
        combat = json.loads((ROOT / "godot/generated/fighters/kakashi/combat.json").read_text())
        self.assertEqual(len(actions["motion_windows"]), 12)
        self.assertEqual(actions["motion_windows"], combat["motion_windows"])

    def test_frame_one_projectile_locals_are_compiled_for_every_artifact(self):
        bundle = json.loads((ROOT / "scripts/fighter/yihu.json").read_text())
        clip = parse_clip_timeline(bundle, 99)
        self.assertEqual(clip["initial_variables"], {"movspeed": 18, "played": 0})
        self.assertEqual(clip["stop_frames"], [1, 10])
        self.assertEqual(clip["rename_frames"][0]["frame"], 5)
        self.assertNotIn("initial_played", clip)
        for role in ("minren", "rifagu", "yihu", "byakuya"):
            for path in (ROOT / f"godot/generated/fighters/{role}").glob("*_controller/controller.json"):
                model = json.loads(path.read_text())
                for hook in model["projectile_hooks"]:
                    projectile = hook["projectile"]
                    self.assertNotIn("initial_played", projectile)
                    if role == "yihu" and projectile.get("character_id") == 99:
                        self.assertEqual(projectile["initial_variables"], clip["initial_variables"])
        for path in ["data/actions/yihu-base.json", "godot/generated/fighters/yihu/combat.json"]:
            projectiles = json.loads((ROOT / path).read_text())["projectiles"]
            self.assertEqual(len(projectiles), 3)
            for projectile in projectiles:
                self.assertEqual(projectile["initial_variables"], clip["initial_variables"])
                self.assertTrue(projectile["on_hit_goto_grouped"])
                self.assertEqual(projectile["on_hit_events"][0]["goto_frame"], 5)

    def test_frame_one_pattern_is_shared_across_source_bundles(self):
        pattern = re.compile(r"stop\(\);\s*var movspeed = (-?\d+(?:\.\d+)?);\s*var played = 0;")
        matched = 0
        for path in (ROOT / "scripts/fighter").glob("*.json"):
            bundle = json.loads(path.read_text())
            for script in bundle["scripts"]:
                match = pattern.fullmatch(script["source"].strip())
                if match is None:
                    continue
                sprite = int(re.match(r"DefineSprite_(\d+)/", script["path"])[1])
                with self.subTest(bundle=path.name, source=script["path"]):
                    clip = parse_clip_timeline(bundle, sprite)
                    self.assertEqual(clip["initial_variables"], {"movspeed": float(match[1]), "played": 0})
                matched += 1
        self.assertGreater(matched, 1)

    def test_implicit_and_explicit_self_hit_test_have_the_same_receiver(self):
        bundle = json.loads((ROOT / "scripts/fighter/Kakashi.json").read_text())
        source = next(row["source"] for row in bundle["scripts"]
                      if row["path"] == "DefineSprite_710/frame_425/PlaceObject2_244_32/CLIPACTIONRECORD onClipEvent(enterFrame).as")
        implicit = parse_projectile_motion(source)
        explicit = parse_projectile_motion(source.replace("hitTest(", "this.hitTest("))
        expected = [{"receiver": "self", "target": name}
                    for name in ["bdmn", "zh1atm", "zh2atm", "zh3atm", "abcd"]]
        self.assertEqual(implicit["collision_queries"], expected)
        self.assertEqual(explicit["collision_queries"], expected)
        child = parse_projectile_motion(source.replace("hitTest(", "box.hitTest("))
        self.assertTrue(all(query["receiver"] == "box" for query in child["collision_queries"]))

    def test_shipped_projectile_queries_and_locals_match_source(self):
        for role, source_role in [("kakashi", "Kakashi"), ("sakura", "Sakura")]:
            bundle = json.loads((ROOT / f"scripts/fighter/{source_role}.json").read_text())
            scripts = {row["path"]: row["source"] for row in bundle["scripts"]}
            for mode in ["ai_controller", "player_controller"]:
                model = json.loads((ROOT / f"godot/generated/fighters/{role}/{mode}/controller.json").read_text())
                for hook in model["projectile_hooks"]:
                    source = scripts.get(hook["path"], "")
                    motion = parse_projectile_motion(source)
                    if motion is None:
                        continue
                    with self.subTest(role=role, mode=mode, path=hook["path"]):
                        for key, value in motion.items():
                            self.assertEqual(hook["projectile"][key], value)
                        load = scripts.get(hook["path"].replace("onClipEvent(enterFrame)", "onClipEvent(load)"), "")
                        initial = parse_projectile_initialization(load)
                        for key, value in (initial or {}).items():
                            self.assertEqual(hook["projectile"][key], value)

    def test_all_shipped_projectile_fields_match_their_source(self):
        sources = {}
        bundles = {}
        timelines = {}
        for path in (ROOT / "scripts/fighter").glob("*.json"):
            bundle = json.loads(path.read_text())
            bundles[Path(bundle["game_file"]).stem.lower()] = bundle
            sources[Path(bundle["game_file"]).stem.lower()] = {
                row["path"]: row["source"] for row in bundle["scripts"]}
        paths = list((ROOT / "godot/generated/fighters").rglob("*.json"))
        paths += list((ROOT / "data/actions").glob("*-base.json"))
        for path in paths:
            text = path.read_text()
            if '"collision_queries"' not in text:
                continue
            role = (path.stem.removesuffix("-base").lower() if path.parent.name == "actions"
                    else path.relative_to(ROOT / "godot/generated/fighters").parts[0])

            def check(node, source_path=""):
                if isinstance(node, dict):
                    source_path = node.get("source_path", node.get("path", source_path))
                    if "collision_queries" in node:
                        if role not in timelines:
                            timelines[role] = json.loads((ROOT / f"data/slices/{role}-base.timeline.json").read_text())
                        timeline = timelines[role]
                        definition = next((d for d in timeline.get("definitions", [])
                                           if d.get("character_id") == node.get("character_id")), {})
                        compiled = parse_projectile_motion(sources[role][source_path], definition.get("frame_labels", {}))
                        with self.subTest(file=str(path.relative_to(ROOT)), source=source_path):
                            load_path = source_path.replace("onClipEvent(enterFrame)", "onClipEvent(load)")
                            initial = parse_projectile_initialization(sources[role].get(load_path, ""))
                            frame_initial = {}
                            if node.get("character_id"):
                                bundle = bundles[role]
                                frame_initial = parse_clip_timeline(bundle, node["character_id"])
                            for key, value in {**compiled, **(initial or {}), **frame_initial}.items():
                                self.assertEqual(node.get(key), value, key)
                    for value in node.values():
                        check(value, source_path)
                elif isinstance(node, list):
                    for value in node:
                        check(value, source_path)

            check(json.loads(text))
