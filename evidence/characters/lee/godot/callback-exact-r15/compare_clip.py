#!/usr/bin/env python3
"""Compare the recorded source clip callback window with the native observer."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
RUN_ID = "lee-callback-lifecycle-recovery-r01"
SOURCE_PATH = "DefineSprite_518/frame_1133/PlaceObject2_18_30/CLIPACTIONRECORD onClipEvent(enterFrame).as"
CASE_ID = "recovery-dash-p2-clip1133-body1134-1144"
sys.path.insert(0, str(ROOT / "tools/probes"))
from collect_ai_reference import decode_number
from event_tape import parse_event_line


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_source(raw: Path) -> list[dict]:
    events = []
    for line in raw.read_text().splitlines():
        if not line.startswith(("AIREF|", "{")):
            continue
        event = parse_event_line(line)
        if event["run_id"] != RUN_ID or event["kind"] != "schedule":
            continue
        values = event["value"].split(",")
        if len(values) < 6 or not values[0].endswith(SOURCE_PATH):
            continue
        instance = values[2]
        if instance != "_level0.game.p2.mc.instance572":
            raise SystemExit(f"unexpected source clip instance: {instance}")
        events.append({
            "source_path": values[0].split("#", 1)[1],
            "phase": values[1],
            "slot": "p2",
            "child_local_frame": int(values[3]),
            "parent_frame": int(values[5]),
            "sequence": event["sequence"],
            "source_display_tick": event["display_tick"],
            "source_fight_tick": event["fight_tick"],
        })
    return events


def parse_body(raw: Path) -> list[dict]:
    events = []
    for line in raw.read_text().splitlines():
        if not line.startswith(("AIREF|", "{")):
            continue
        event = parse_event_line(line)
        if event["run_id"] != RUN_ID or event["kind"] != "body_boundary":
            continue
        values = event["value"].split(",")
        if len(values) < 7 or values[0] != "p2" or int(values[1]) not in (1134, 1144):
            continue
        events.append({
            "source_frame": int(values[1]),
            "entering": values[2] == "true",
            "action": float(decode_number(values[4])),
            "ql": float(decode_number(values[6])),
            "source_sequence": event["sequence"],
            "source_display_tick": event["display_tick"],
            "source_fight_tick": event["fight_tick"],
        })
    return events


pre = json.loads((HERE / "preflight.json").read_text())
case = pre["cases"][0]
raw = ROOT / case["source_raw"] / "events.jsonl"
build_path = ROOT / case["source_build_copy"]
instrumentation = ROOT / case["source_instrumentation_copy"]
fixture_path = ROOT / case["fixture"]
build = json.loads(build_path.read_text())
fixture = json.loads(fixture_path.read_text())
raw_lines = raw.read_text().splitlines()
done = any(line.endswith("|done|") for line in raw_lines)
if not done:
    raise SystemExit("source capture has no terminal done marker")
if sha(raw) != case["source_raw_sha256"]:
    raise SystemExit("source raw SHA mismatch")
if sha(build_path) != case["source_build_sha256"]:
    raise SystemExit("source build SHA mismatch")
if sha(instrumentation) != case["source_instrumentation_sha256"]:
    raise SystemExit("source instrumentation SHA mismatch")
if build.get("run_id") != RUN_ID:
    raise SystemExit("source build/run id mismatch")
if build.get("outputs_sha256", {}).get("game/main.swf") != case["source_output_main_sha256"]:
    raise SystemExit("source SWF output SHA mismatch")

source = parse_source(raw)
source_body = parse_body(raw)
out = HERE / "out" / f"{CASE_ID}.json.clips.json"
native_payload = json.loads(out.read_text())
native = native_payload["callback_events"]
engine_log = (HERE / "engine.log").read_text()
native_summary = None
for line in engine_log.splitlines():
    if line.startswith("LEE_EXACT_CALLBACK_SUMMARY "):
        item = json.loads(line.split(" ", 1)[1])
        if item.get("fixture") == CASE_ID:
            native_summary = item["events"]
if native_summary is None:
    raise SystemExit("missing native frame-action callback summary")
native_rows = [{
    "source_path": event["source_path"],
    "phase": event["phase"],
    "slot": event["slot"],
    "child_local_frame": int(event["child_placement"]["child_local_frame"]),
    "parent_frame": int(event["parent_frame"]),
} for event in native]
source_rows = [{key: event[key] for key in (
    "source_path", "phase", "slot", "child_local_frame", "parent_frame")}
    for event in source]
source_body_rows = [{key: event[key] for key in ("source_frame", "entering", "action", "ql")}
                    for event in source_body]
native_body_rows = [{key: event[key] for key in ("source_frame", "entering", "action", "ql")}
                    for event in native_summary]

source_move = case["source_move_case"]
native_inputs_match = (
    fixture["fighters"] == source_move["fighters"]
    and fixture["setup"] == source_move["setup"]
    and fixture["inputs"] == [
        {"slot": item["slot"], "keys": item["keys"], "start": item["start"], "end": item["end"]}
        for item in source_move["inputs"]
    ]
    and fixture["p1_helper"] == source_move["p1_helper"]
    and fixture["p2_helper"] == source_move["p2_helper"]
    and fixture["frames"] == case["actual_capture_frames"]
    and build.get("configuration") == case["source_build_config"]
    and build.get("move_case") == source_move
)

lifetimes = native_payload["lifetime_events"]
if not lifetimes:
    raise SystemExit("native clip lifetime observer produced no events")
first = lifetimes[0]
life_shape = [
    (row["phase"], int(row["parent_frame"]), row["slot"], row["source_path"],
     int(row["placement"].get("character_id", -1)), int(row["placement"].get("depth", -1)),
     int(row["placement"].get("child_local_frame", -1)), int(row["generation"]),
     int(row["registration_id"]))
    for row in lifetimes
]
expected_lifetimes = [
    ("placed", 1133, "p2", SOURCE_PATH, 18, 30, 1,
     int(first["generation"]), int(first["registration_id"])),
    ("removed", 1138, "p2", SOURCE_PATH, -1, -1, -1,
     int(first["generation"]), int(first["registration_id"])),
]
registry_audit = native_payload["registry_install_audit"]
if not registry_audit.get("same_registration_order_and_placed_tick"):
    raise SystemExit("test-only registry replacement changed inherited registration order/phase")

batch_done = "MOVE_CASE_BATCH_OK 1" in engine_log
errors = [line for line in engine_log.splitlines() if "SCRIPT ERROR" in line]
report = {
    "schema": "lee-callback-clip-exact-r15",
    "scope": "The source and native callback cadence is compared for one same-source P2 recovery fixture. Native placement lifetime and registration behavior are reported separately; the source tape does not directly record clip removal.",
    "source_run_id": RUN_ID,
    "case_id": CASE_ID,
    "runtime_files": {
        path: sha(ROOT / path) for path in (
            "godot/source_callback_registry.gd",
            "godot/tests/callback_trace_registry.gd",
            "godot/tests/lee_callback_exact_probe.gd",
        )
    },
    "test_and_compare_tool_hashes": {
        path: sha(HERE / path) for path in (
            "event_tape.py", "event_tape_smoke.py", "compare_clip.py",
            "update_inventory.py",
        )
    } | {
        "godot/tests/callback_trace_registry_smoke.gd": sha(ROOT / "godot/tests/callback_trace_registry_smoke.gd"),
    },
    "source_provenance": {
        "raw": str(raw.relative_to(ROOT)),
        "raw_sha256": sha(raw),
        "build": str(build_path.relative_to(ROOT)),
        "build_sha256": sha(build_path),
        "instrumentation_sha256": sha(instrumentation),
        "source_main_swf_sha256": case["source_output_main_sha256"],
        "done_marker": done,
    },
    "native_provenance": {
        "fixture": str(fixture_path.relative_to(ROOT)),
        "fixture_sha256": sha(fixture_path),
        "fixture_input_setup_helpers_match_source": native_inputs_match,
        "engine_log_sha256": sha(HERE / "engine.log"),
        "engine_exitcode": 0 if batch_done and not errors else None,
        "script_errors": errors,
        "event_tape_smoke_ok": (HERE / "event-tape-smoke.log").is_file()
            and "AIREF_EVENT_TAPE_SMOKE_OK" in (HERE / "event-tape-smoke.log").read_text(),
        "callback_registry_smoke_ok": "CALLBACK_TRACE_REGISTRY_SMOKE_OK" in (HERE / "callback-trace-registry-smoke.log").read_text(),
    },
    "callback_comparison": {
        "status": "exact_0diff" if source_rows == native_rows and native_inputs_match and batch_done and not errors else "diverged_or_invalid",
        "fields": ["source_path", "phase", "slot", "parent_frame", "child_local_frame"],
        "source_events": source,
        "native_events": native,
        "source_count": len(source),
        "native_count": len(native),
        "diffs": [
            {"index": index, "source": source_rows[index] if index < len(source_rows) else None,
             "native": native_rows[index] if index < len(native_rows) else None}
            for index in range(max(len(source_rows), len(native_rows)))
            if (source_rows[index] if index < len(source_rows) else None)
            != (native_rows[index] if index < len(native_rows) else None)
        ],
    },
    "body_boundary_comparison": {
        "status": "exact_0diff" if source_body_rows == native_body_rows and native_inputs_match and batch_done and not errors else "diverged_or_invalid",
        "fields": ["source_frame", "entering", "action", "ql"],
        "source_events": source_body,
        "native_events": native_summary,
        "source_count": len(source_body),
        "native_count": len(native_summary),
        "diffs": [
            {"index": index, "source": source_body_rows[index] if index < len(source_body_rows) else None,
             "native": native_body_rows[index] if index < len(native_body_rows) else None}
            for index in range(max(len(source_body_rows), len(native_body_rows)))
            if (source_body_rows[index] if index < len(source_body_rows) else None)
            != (native_body_rows[index] if index < len(native_body_rows) else None)
        ],
    },
    "native_lifecycle_observation": {
        "status": "observed" if life_shape == expected_lifetimes else "unexpected",
        "fields": ["phase", "parent_frame", "slot", "source_path", "character_id", "depth", "child_local_frame", "generation", "registration_id"],
        "events": lifetimes,
        "source_removal_marker_available": False,
    },
    "test_registry_injection": registry_audit,
}
(HERE / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({
    "callback_status": report["callback_comparison"]["status"],
    "body_status": report["body_boundary_comparison"]["status"],
    "source_events": len(source), "native_events": len(native),
    "native_lifecycle": report["native_lifecycle_observation"]["status"],
    "same_registry_order_and_placed_tick": registry_audit["same_registration_order_and_placed_tick"],
}, ensure_ascii=False))
if (report["callback_comparison"]["status"] != "exact_0diff"
        or report["body_boundary_comparison"]["status"] != "exact_0diff"
        or report["native_lifecycle_observation"]["status"] != "observed"
        or not report["native_provenance"]["event_tape_smoke_ok"]
        or not report["native_provenance"]["callback_registry_smoke_ok"]):
    raise SystemExit(1)
