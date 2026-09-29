from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import analyze_diagnostics as diagnostics  # noqa: E402


class AnalyzeDiagnosticsTests(unittest.TestCase):
    def test_reads_legacy_v1_combat_events_without_inventing_ticks_or_global_pause(self) -> None:
        report = {
            "schemaVersion": 1,
            "startedAt": "2026-09-14T15:00:00Z",
            "exportedAt": "2026-09-14T15:01:00Z",
            "droppedEntries": 2,
            "entries": [
                {"time": "2026-09-14T15:00:01Z", "level": "error", "message": "test error"},
                {"time": "2026-09-14T15:00:02Z", "level": "log", "message": 'COMBAT_EVENT {"event":"hit_settlement","fighter":"佐助","frame":875,"zhanting":false}'},
            ],
        }
        summary = diagnostics.analyze_report(report)
        self.assertEqual(summary["legacyCombatEvents"]["count"], 1)
        self.assertEqual(summary["legacyCombatEvents"]["types"], {"hit_settlement": 1})
        self.assertFalse(summary["legacyCombatEvents"]["fightTickAvailable"])
        self.assertEqual(summary["replayability"]["exactReplayCandidate"], False)
        self.assertTrue(any("fighter-local" in note and "global pause" in note for note in summary["notes"]))
        self.assertEqual(summary["entries"]["errors"][0]["message"], "test error")

    def test_summarizes_v2_match_build_events_and_replay_gaps(self) -> None:
        report = self._v2_report()
        summary = diagnostics.analyze_report(report)
        self.assertEqual(summary["build"]["status"], "match")
        self.assertEqual(summary["runtime"]["match"]["modeName"], "versus")
        self.assertEqual(summary["runtime"]["eventTypes"], {"input_consumed": 1, "pause_state": 1})
        self.assertEqual(summary["runtime"]["inputCount"], 1)
        self.assertTrue(any("complete scene-restoration" in warning for warning in summary["replayability"]["warnings"]))

    def test_reports_replay_diagnostics_and_online_performance_separately(self) -> None:
        report = self._v2_report()
        report["runtime"]["events"].extend([
            {"seq": 3, "type": "hit_settled", "fightTick": 12,
             "payload": {"replay": True, "damage": 90}},
            {"seq": 4, "type": "online_performance", "fightTick": 12,
             "payload": {
                 "schemaVersion": 2,
                 "rollbackWork": {"windowDelta": {"advance_count": 4, "replay_advance_count": 2}},
                 "sync": {
                     "ticks": {"remoteMessages": 2, "corrections": 1,
                               "remoteMessagesPerTick": {"p95": 1},
                               "correctionsPerTick": {"p95": 1}},
                     "transportDrains": {"count": 1, "messagesDelivered": 2, "corrections": 1,
                                         "messagesPerDrain": {"p95": 2},
                                         "correctionsPerDrain": {"p95": 1}},
                     "inputArrivalLead": {"p5": -2, "p50": 0, "p95": 1},
                     "frameAdvantage": {"p50": 3, "p95": 4, "max": 4},
                 },
             }},
        ])

        summary = diagnostics.analyze_report(report)
        self.assertEqual(summary["runtime"]["eventCount"], 4)
        self.assertEqual(summary["runtime"]["replayEvents"]["count"], 1)
        self.assertEqual(summary["runtime"]["onlinePerformance"]["count"], 1)
        self.assertEqual(summary["runtime"]["onlinePerformance"]["latest"]["rollbackWork"]["windowDelta"]["replay_advance_count"], 2)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            diagnostics._print_result(summary, as_json=False)
        rendered = output.getvalue()
        self.assertIn("Replay-tagged diagnostic events: 1", rendered)
        self.assertIn("original predicted event", rendered)
        self.assertIn("rollbackWork delta={'advance_count': 4, 'replay_advance_count': 2}", rendered)
        self.assertIn("arrivalLead p5/p50/p95=-2/0/1", rendered)

    def test_compare_reports_first_event_and_checkpoint_difference(self) -> None:
        left = self._v2_report()
        right = self._v2_report()
        right["runtime"]["events"][1]["payload"]["reason"] = "different"
        right["runtime"]["snapshot"]["match"]["players"]["p1"]["hp"] = 700
        result = diagnostics.compare_reports(left, right)
        self.assertEqual(result["firstEventDifference"]["index"], 1)
        self.assertEqual(result["firstSnapshotDifference"]["path"], "$.players.p1.hp")
        self.assertIn("not a source-parity verdict", result["mode"])

    def test_snapshot_compare_treats_godot_integer_float_json_values_equally(self) -> None:
        self.assertIsNone(diagnostics._first_json_difference({"energy": 0}, {"energy": 0.0}))
        self.assertEqual(diagnostics._first_json_difference({"energy": 0}, {"energy": 0.5})["path"], "$.energy")

    def test_load_rejects_unknown_schema_and_non_object_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "report.json"
            path.write_text('{"schemaVersion":99}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsupported diagnostics schemaVersion"):
                diagnostics.load_report(path)
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be an object"):
                diagnostics.load_report(path)

    def test_cli_analyzes_the_historical_user_log(self) -> None:
        historical = Path("/Users/fengkx/Downloads/bvn26-log-2026-09-14T16-00-55-416Z.json")
        if not historical.is_file():
            self.skipTest("Historical user log is not available in this environment")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = diagnostics.main(["analyze", str(historical), "--json"])
        self.assertEqual(result, 0)
        summary = json.loads(output.getvalue())
        self.assertEqual(summary["schemaVersion"], 1)
        self.assertEqual(summary["legacyCombatEvents"]["count"], 443)
        self.assertFalse(summary["replayability"]["exactReplayCandidate"])
        self.assertTrue(any("fighter-local" in note for note in summary["notes"]))

    def test_native_main_capture_reports_fresh_start_coverage_and_last_hit(self) -> None:
        native_capture = Path("/private/tmp/bvn-diagnostic-main-r05.json")
        if not native_capture.is_file():
            self.skipTest("Native Main diagnostic capture is not available in this environment")
        summary = diagnostics.analyze_report(diagnostics.load_report(native_capture))
        self.assertEqual(summary["runtime"]["eventCount"], 824)
        self.assertEqual(summary["runtime"]["inputCount"], 800)
        self.assertEqual(summary["runtime"]["randomEventCount"], 5)
        self.assertEqual(summary["runtime"]["clockEventCount"], 0)
        self.assertEqual(summary["runtime"]["match"]["fightTick"], 400)
        self.assertEqual(summary["runtime"]["lastHit"]["fightTick"], 350)
        self.assertTrue(summary["replayability"]["freshStartRecipeAvailable"])
        self.assertTrue(summary["replayability"]["freshReplayPrerequisitesComplete"])
        self.assertEqual(summary["replayability"]["executorVerdict"], "not_run")

    def test_replay_preflight_requires_matching_build_and_catalog_resolved_resources(self) -> None:
        native_capture = Path("/private/tmp/bvn-diagnostic-main-r05.json")
        if not native_capture.is_file():
            self.skipTest("Native Main diagnostic capture is not available in this environment")
        report = diagnostics.load_report(native_capture)
        build_id = "a" * 64
        resource_version = "c" * 64
        source_hash = resource_version
        report["build"] = {
            "status": "match", "buildID": build_id, "sidecarBuildID": build_id,
            "pckSha256": "b" * 64, "pckHashKind": "exported_artifact",
            "resourceVersion": resource_version,
        }
        for event in report["runtime"]["events"]:
            event["buildID"] = build_id
        report["runtime"]["snapshot"]["buildID"] = build_id
        start_match = next(event for event in report["runtime"]["events"] if event["type"] == "match_started")["payload"]["match"]
        start_match["resourceVersion"] = resource_version
        report["runtime"]["snapshot"]["match"]["resourceVersion"] = resource_version
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            generated = project / "generated"
            generated.mkdir()
            (generated / "build_metadata.json").write_text(json.dumps({
                "schemaVersion": 1, "buildID": build_id, "resourceVersion": resource_version,
                "sourceTreeSha256": source_hash,
            }), encoding="utf-8")
            roster_path = generated / "main/character_selection/available.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text((ROOT / "godot/generated/main/character_selection/available.json").read_text(encoding="utf-8"), encoding="utf-8")
            stage_catalog = generated / "stages/catalog/catalog.json"
            stage_catalog.parent.mkdir(parents=True)
            stage_catalog.write_text(json.dumps({"stages": [{"id": "现世"}]}), encoding="utf-8")
            with mock.patch.object(diagnostics, "sha256_tree", return_value=resource_version):
                self.assertEqual(diagnostics.replay_preflight(report, project), [])

                next(event for event in report["runtime"]["events"] if event["type"] == "match_started")["payload"]["match"]["players"]["p1"]["resourcePath"] = "res://user-provided/script"
                problems = diagnostics.replay_preflight(report, project)
                self.assertTrue(any("resource path" in problem for problem in problems))

    def test_replay_preflight_rejects_cpu_modes_not_recorded_as_inputs(self) -> None:
        report = self._v2_report()
        start_match = report["runtime"]["snapshot"]["match"]
        start_match.update({"mode": 4, "modeName": "vs_com", "p2cpu": True})
        report["runtime"]["events"].insert(0, {
            "seq": 0, "type": "match_started", "payload": {"match": start_match},
        })
        problems = diagnostics.replay_preflight(report, ROOT / "godot")
        self.assertTrue(any("Unsupported replay mode" in problem for problem in problems))
        self.assertTrue(any("p2 must be a human-controlled" in problem for problem in problems))

    def test_replay_invokes_only_fixed_executor_without_shell(self) -> None:
        report = self._v2_report()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "input report.json"
            source.write_text(json.dumps(report), encoding="utf-8")
            output = directory / "result.json"
            executable = directory / "Godot"
            executable.write_text("", encoding="utf-8")
            project = directory / "project"
            project.mkdir()
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")

            def fake_run(command, **kwargs):
                Path(command[-1]).write_text(json.dumps({"replay": {"status": "exact_match"}}), encoding="utf-8")
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch.object(diagnostics, "replay_preflight", return_value=[]), mock.patch.object(diagnostics.subprocess, "run", side_effect=fake_run) as run:
                status, result = diagnostics.run_replay(
                    source, report, godot_executable=str(executable), output_path=output,
                    project_path=project,
                    log_path=directory / "godot log.txt", timeout_seconds=10,
                )
            self.assertEqual(status, 0)
            self.assertEqual(result["status"], "exact_match")
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("-s") + 1], str((ROOT / "godot/tests/diagnostic_replay_smoke.gd").resolve()))
            self.assertEqual(command[command.index("--path") + 1], str(project.resolve()))
            self.assertNotIn("shell", run.call_args.kwargs)
            self.assertEqual(command[-2], str(source.resolve()))

            divergent_output = directory / "diverged.json"

            def fake_divergence(command, **kwargs):
                Path(command[-1]).write_text(json.dumps({"replay": {
                    "status": "diverged", "firstDifference": {"index": 3},
                }}), encoding="utf-8")
                return mock.Mock(returncode=1, stdout="", stderr="")

            with mock.patch.object(diagnostics, "replay_preflight", return_value=[]), mock.patch.object(diagnostics.subprocess, "run", side_effect=fake_divergence):
                status, result = diagnostics.run_replay(
                    source, report, godot_executable=str(executable), output_path=divergent_output,
                    project_path=project, log_path=directory / "diverged.log", timeout_seconds=10,
                )
            self.assertEqual(status, 1)
            self.assertEqual(result["status"], "diverged")
            self.assertEqual(result["executorResult"]["replay"]["firstDifference"], {"index": 3})

    @staticmethod
    def _v2_report() -> dict:
        build_id = "a" * 64
        resource_version = diagnostics.sha256_tree(ROOT / "godot/generated", exclude={Path("build_metadata.json")})
        return {
            "schemaVersion": 2,
            "runId": "run-test",
            "startedAt": "2026-09-15T00:00:00Z",
            "exportedAt": "2026-09-15T00:00:10Z",
            "build": {
                "status": "match", "buildID": build_id, "sidecarBuildID": build_id,
                "pckSha256": "b" * 64, "pckHashKind": "exported_artifact",
                "resourceVersion": resource_version,
            },
            "entries": [],
            "runtime": {
                "snapshotStatus": "acknowledged",
                "snapshot": {
                    "buildID": build_id,
                    "match": {
                        "matchId": "match-test",
                        "mode": 3,
                        "modeName": "versus",
                        "p1cpu": False,
                        "p2cpu": False,
                        "map": "现世",
                        "resourceVersion": resource_version,
                        "players": {
                            "p1": {"slot": "p1", "fighter": "春野樱", "resourcePath": "res://generated/fighters/sakura", "hp": 800, "zhanting": False},
                            "p2": {"slot": "p2", "fighter": "鸣人", "resourcePath": "res://generated/fighters/minren", "hp": 800},
                        },
                        "pause": {"globalSuper": False, "user": False},
                        "replayability": {"completeCheckpoint": False},
                    },
                },
                "events": [
                    {"seq": 1, "type": "input_consumed", "fightTick": 10, "buildID": build_id, "payload": {"slot": "p1", "keys": ["J"]}},
                    {"seq": 2, "type": "pause_state", "fightTick": 11, "buildID": build_id, "payload": {"reason": "user_pause"}},
                ],
                "inputTape": [{"seq": 1, "type": "input_consumed", "fightTick": 10, "buildID": build_id, "payload": {"slot": "p1", "keys": ["J"]}}],
                "buffer": {"retainedEvents": 2, "dropped": {"age": 0, "count": 0, "bytes": 0}, "rejectedEvents": 0},
            },
        }


if __name__ == "__main__":
    unittest.main()
