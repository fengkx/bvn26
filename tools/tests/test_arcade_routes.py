import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ArcadeRoutesTest(unittest.TestCase):
    def test_all_encounters_match_flash(self):
        campaign = json.loads((ROOT / "godot/generated/main/arcade/campaign.json").read_text())
        actual = {}
        for player, route in campaign["routes"].items():
            self.assertEqual(len(route), 8)
            for stage, encounter_id in enumerate(route):
                encounter = campaign["encounters"][encounter_id]
                actual[player, stage] = (encounter["fighter"], encounter["helper"], encounter["map"])
        with (ROOT / "evidence/arcade/routes.tsv").open() as stream:
            expected = {
                (row["player"], int(row["stage_index"])): (row["opponent"], row["helper"], row["map"])
                for row in csv.DictReader(stream, delimiter="\t")
            }
        self.assertEqual(len(expected), 320)
        self.assertEqual(actual, expected)
