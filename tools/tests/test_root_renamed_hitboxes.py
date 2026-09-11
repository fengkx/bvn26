"""Root timeline instance renames retain source hitbox lifetimes."""

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/importer"))
from build_combat_model import _merge_root_atm_windows


def frame(number, placement=None):
    return {
        "frame": number,
        "display_list": [] if placement is None else [placement],
    }


class RootRenamedHitboxTests(unittest.TestCase):
    def test_same_instance_non_attack_rename_ends_window(self):
        placement = {
            "depth": 7,
            "character_id": 488,
            "name": "dogs",
            "placed_frame": 10,
        }
        timeline = {n: frame(n, placement) for n in range(10, 18)}
        scripts = [
            {
                "kind": "frame_action",
                "action": "上必杀",
                "frame": 11,
                "path": "frame_11.as",
                "source": 'dogs._name = "sbsatm";',
                "source_sha256": "attack",
            },
            {
                "kind": "frame_action",
                "action": "上必杀",
                "frame": 14,
                "path": "frame_14.as",
                "source": 'sbsatm._name = "dogs";',
                "source_sha256": "visual",
            },
        ]

        hitboxes = {}
        _merge_root_atm_windows(
            hitboxes,
            {"上必杀": {"start_frame": 10, "end_frame": 17}},
            timeline,
            scripts,
        )

        self.assertEqual([(item["start_frame"], item["end_frame"])
                          for item in hitboxes["上必杀"]], [(11, 13)])

    def test_old_name_write_is_undefined_and_does_not_end_window(self):
        placement = {
            "depth": 7,
            "character_id": 488,
            "name": "dogs",
            "placed_frame": 10,
        }
        timeline = {n: frame(n, placement) for n in range(10, 18)}
        scripts = [
            {
                "kind": "frame_action", "action": "上必杀", "frame": 11,
                "path": "frame_11.as", "source": 'dogs._name = "sbsatm";',
                "source_sha256": "attack",
            },
            {
                "kind": "frame_action", "action": "上必杀", "frame": 14,
                "path": "frame_14.as", "source": 'dogs._name = "dogs";',
                "source_sha256": "stale",
            },
        ]
        hitboxes = {}
        _merge_root_atm_windows(
            hitboxes, {"上必杀": {"start_frame": 10, "end_frame": 17}},
            timeline, scripts,
        )
        self.assertEqual(hitboxes["上必杀"][0]["end_frame"], 17)

    def test_controlled_root_rename_fails_closed(self):
        placement = {
            "depth": 7,
            "character_id": 488,
            "name": "dogs",
            "placed_frame": 10,
        }
        timeline = {n: frame(n, placement) for n in range(10, 18)}
        scripts = [{
            "kind": "frame_action",
            "action": "上必杀",
            "frame": 11,
            "path": "frame_11.as",
            "source": 'if (enabled) {\n  dogs._name = "sbsatm";\n}',
            "source_sha256": "controlled",
        }]

        with self.assertRaisesRegex(ValueError, "controlled root rename"):
            _merge_root_atm_windows(
                {},
                {"上必杀": {"start_frame": 10, "end_frame": 17}},
                timeline,
                scripts,
            )

    def test_rename_ends_when_depth_is_replaced(self):
        old = {
            "depth": 7,
            "character_id": 488,
            "name": "dogs",
            "placed_frame": 10,
        }
        replacement = {**old, "character_id": 499, "placed_frame": 13}
        timeline = {
            n: frame(n, old if n < 13 else replacement)
            for n in range(10, 21)
        }
        scripts = [{
            "kind": "frame_action",
            "action": "上必杀",
            "frame": 11,
            "path": "DefineSprite_710/frame_11/DoAction.as",
            "source": 'dogs._name = "sbsatm";',
            "source_sha256": "root-rename",
        }]

        hitboxes = {}
        _merge_root_atm_windows(
            hitboxes,
            {"上必杀": {"start_frame": 10, "end_frame": 20}},
            timeline,
            scripts,
        )

        self.assertEqual(hitboxes["上必杀"], [{
            "instance_name": "sbsatm",
            "start_frame": 11,
            "end_frame": 12,
            "placed_name": "dogs",
            "character_id": 488,
            "depth": 7,
            "placed_frame": 10,
            "source_path": "DefineSprite_710/frame_11/DoAction.as",
            "source_sha256": "root-rename",
        }])

    def test_reused_depth_gets_a_new_window(self):
        old = {
            "depth": 7,
            "character_id": 488,
            "name": "dogs",
            "placed_frame": 10,
        }
        new = {**old, "placed_frame": 15}
        timeline = {
            n: frame(n, old if n < 13 else (None if n < 15 else new))
            for n in range(10, 19)
        }
        scripts = [
            {
                "kind": "frame_action",
                "action": "上必杀",
                "frame": 11,
                "path": "old.as",
                "source": 'dogs._name = "sbsatm";',
                "source_sha256": "old",
            },
            {
                "kind": "frame_action",
                "action": "上必杀",
                "frame": 16,
                "path": "new.as",
                "source": 'dogs._name = "sbsatm";',
                "source_sha256": "new",
            },
        ]

        hitboxes = {}
        _merge_root_atm_windows(
            hitboxes,
            {"上必杀": {"start_frame": 10, "end_frame": 18}},
            timeline,
            scripts,
        )

        self.assertEqual(
            [(item["start_frame"], item["end_frame"], item["source_sha256"])
             for item in hitboxes["上必杀"]],
            [(11, 12, "old"), (16, 18, "new")],
        )


if __name__ == "__main__":
    unittest.main()
