"""Regression against retained, unmodified source and executed replay reports."""
import copy
import gzip
import json
import tempfile
import unittest
from pathlib import Path

from tools.probes.validate_ai_continuous_replay import validate

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "evidence/ai/input-binary-r13/events.jsonl"
BUILD = SOURCE.with_name("build.json")


def load(path):
    return json.loads(gzip.decompress(path.read_bytes()))


class ReadyReportTests(unittest.TestCase):
    def setUp(self):
        self.report = load(HERE / "replay.json.gz")

    def validate_report(self, report):
        with tempfile.TemporaryDirectory() as directory:
            replay = Path(directory) / "replay.json"
            replay.write_text(json.dumps(report))
            return validate(SOURCE, replay, 600, BUILD)

    def test_actual_state_and_cursor_are_now_checkable(self):
        result = self.validate_report(self.report)
        self.assertTrue(result["checks"]["post_ready_states"]["matched"])
        self.assertTrue(result["checks"]["post_ready_geometry"]["matched"])
        self.assertTrue(result["checks"]["random_consumers"]["scope_complete"])
        self.assertEqual(self.report["native_checkpoint"]["display_tick"], 484)
        self.assertEqual(self.report["native_checkpoint"]["random_absolute_index"], 95)
        self.assertIsNone(self.report["native_checkpoint"]["actors"][0]["touchFloor"])
        self.assertFalse(result["checks"]["ready_checkpoint"])
        self.assertEqual(len(self.report["native_checkpoint"]["helpers"]), 2)
        self.assertEqual(result["first_reason"], "source_build_provenance_not_clean")
        self.assertEqual(result["status"], "unknown")

    def test_old_differences_only_report_does_not_pass(self):
        old = load(HERE.parent / "replay-runtime-cleanup/bvn-runtime-r13-after.json.gz")
        result = self.validate_report(old)
        self.assertFalse(result["checks"]["post_ready_states"]["matched"])
        self.assertFalse(result["checks"]["ready_checkpoint"])
        self.assertFalse(result["checks"]["random_consumers"]["scope_complete"])
        # Only reporting changed, not simulation or tape consumption.
        for key in ("boundary_comparisons", "geometry_comparisons", "frame_comparisons",
                    "random_consumed", "clock_consumed", "input_transitions"):
            self.assertEqual(old[key], self.report[key])
        for row, previous in zip(self.report["state_comparisons"], old["state_comparisons"]):
            self.assertEqual({key: row[key] for key in previous}, previous)

    def test_changed_actual_state_and_cursor_are_refused(self):
        report = copy.deepcopy(self.report)
        row = next(row for row in report["state_comparisons"] if row["display_tick"] == 484)
        row["actual"]["hp"] = 999
        report["native_checkpoint"]["random_absolute_index"] = 94
        result = self.validate_report(report)
        self.assertFalse(result["checks"]["post_ready_states"]["matched"])
        self.assertFalse(result["checks"]["random_consumers"]["scope_complete"])
        self.assertEqual(result["first_reason"], "source_build_provenance_not_clean")


class ObservationBindingReportTests(unittest.TestCase):
    def test_r13_prior_fields_are_unchanged(self):
        before = load(HERE / "replay.json.gz")
        after = load(HERE / "binding-fix/replay.json.gz")
        self.assertEqual({key: after[key] for key in before}, before)
        self.assertEqual(after["report_failure"], {})
        self.assertEqual(len(after["native_checkpoint"]["helpers"]), 2)
        self.assertIsNone(after["native_checkpoint"]["actors"][0]["touchFloor"])

    def test_actual_refusal_serializes_all_false_flags(self):
        refused = load(HERE / "binding-fix/refusal.json.gz")
        success = load(HERE / "binding-fix/replay.json.gz")
        self.assertEqual(refused["status"], "identity_refused")
        self.assertEqual(refused["native_checkpoint"], {})
        for flag in ("production_admitted", "native_parity_proven", "oracle_accepted",
                     "certified_global_tick", "os_input_join_proven", "original_parity_verified"):
            self.assertIs(refused[flag], False)
            self.assertIs(success[flag], False)


if __name__ == "__main__":
    unittest.main()
