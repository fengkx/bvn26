"""Projectile callbacks query their own current geometry, not receiver history."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
from build_combat_model import parse_projectile_motion, parse_projectile_initialization


class ProjectileContactTests(unittest.TestCase):
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

    def test_all_shipped_collision_queries_match_their_source(self):
        sources = {}
        for path in (ROOT / "scripts/fighter").glob("*.json"):
            bundle = json.loads(path.read_text())
            sources[Path(bundle["game_file"]).stem.lower()] = {
                row["path"]: row["source"] for row in bundle["scripts"]}
        for path in (ROOT / "godot/generated/fighters").rglob("*.json"):
            text = path.read_text()
            if '"collision_queries"' not in text:
                continue
            role = path.relative_to(ROOT / "godot/generated/fighters").parts[0]

            def check(node, source_path=""):
                if isinstance(node, dict):
                    source_path = node.get("source_path", node.get("path", source_path))
                    if "collision_queries" in node:
                        compiled = parse_projectile_motion(sources[role][source_path])
                        with self.subTest(file=str(path.relative_to(ROOT)), source=source_path):
                            self.assertEqual(node["collision_queries"], compiled["collision_queries"])
                    for value in node.values():
                        check(value, source_path)
                elif isinstance(node, list):
                    for value in node:
                        check(value, source_path)

            check(json.loads(text))
