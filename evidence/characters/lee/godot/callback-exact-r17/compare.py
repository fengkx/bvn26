#!/usr/bin/env python3
"""Compare selected exact body-boundary rows on Lee's r04 source input."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
RUN = HERE / (sys.argv[1] if len(sys.argv) > 1 else "retry-01")
sys.path.insert(0, str(ROOT / "evidence/characters/lee/godot/callback-exact-r15"))
from event_tape import parse_event_line
sys.path.insert(0, str(ROOT / "tools/probes"))
from collect_ai_reference import decode_number

pre = json.loads((HERE / "preflight.json").read_text())
raw = ROOT / pre["source_raw"]
build_path = ROOT / pre["source_build"]
source_fixture_path = ROOT / pre["source_fixture"]
instrumentation = ROOT / pre["source_instrumentation"]
native_fixture = ROOT / pre["native_fixture"]
build = json.loads(build_path.read_text())
source_fixture = json.loads(source_fixture_path.read_text())
fixture = json.loads(native_fixture.read_text())
if build.get("run_id") != pre["run_id"] or build.get("outputs_sha256", {}).get("game/main.swf") != pre["source_output_main_sha256"]:
    raise SystemExit("source build identity/output mismatch")
if hashlib.sha256(raw.read_bytes()).hexdigest() != pre["source_raw_sha256"]:
    raise SystemExit("source raw changed after preflight")
if hashlib.sha256(build_path.read_bytes()).hexdigest() != pre["source_build_sha256"]:
    raise SystemExit("source build changed after preflight")
if hashlib.sha256(native_fixture.read_bytes()).hexdigest() != pre["native_fixture_sha256"]:
    raise SystemExit("native fixture changed after preflight")
if source_fixture["fighter"] != build["move_case"]["fighter"] or source_fixture["slot"] != build["move_case"]["slot"]:
    raise SystemExit("source fixture/build identity mismatch")

targets = {62, 128}
source_events = []
for line in raw.read_text().splitlines():
    if not line.startswith(("AIREF|", "{")):
        continue
    event = parse_event_line(line)
    if event["run_id"] != pre["run_id"] or event["kind"] != "body_boundary":
        continue
    values = event["value"].split(",")
    if len(values) < 7 or values[0] != "p1" or int(values[1]) not in targets:
        continue
    source_events.append({
        "source_frame": int(values[1]),
        "entering": values[2] == "true",
        "action": float(decode_number(values[4])),
        "ql": float(decode_number(values[6])),
        "sequence": int(event["sequence"]),
        "fight_tick": int(event["fight_tick"]),
    })
if [(row["source_frame"], row["entering"]) for row in source_events] != [(128, True), (128, False), (62, True), (62, False)]:
    raise SystemExit("source raw target pairs/order do not match the captured source trace")

engine_log = (RUN / "engine.log").read_text()
errors = [line for line in engine_log.splitlines() if "SCRIPT ERROR" in line]
summary = None
for line in engine_log.splitlines():
    if line.startswith("LEE_EXACT_CALLBACK_SUMMARY "):
        item = json.loads(line.split(" ", 1)[1])
        if item.get("fixture") == pre["case_id"]:
            summary = item["events"]
if summary is None:
    raise SystemExit("native target summary missing")
native_events = [row for row in summary if int(row["source_frame"]) in targets and row["slot"] == "p1"]
source_rows = [{key: row[key] for key in ("source_frame", "entering", "action", "ql")} for row in source_events]
native_rows = [{key: row[key] for key in ("source_frame", "entering", "action", "ql")} for row in native_events]

move = pre["source_move_case"]
input_match = (
    fixture.get("fighters") == move.get("fighters")
    and fixture.get("setup") == move.get("setup")
    and fixture.get("inputs") == move.get("inputs")
    and fixture.get("p1_helper") == move.get("p1_helper")
    and fixture.get("p2_helper") == move.get("p2_helper")
    and fixture.get("frames") == move.get("frames")
    and build.get("configuration") == pre["source_build_config"]
)
batch_ok = "MOVE_CASE_BATCH_OK 1" in engine_log and "MOVE_CASE_REFERENCE_OK " + pre["case_id"] in engine_log and not errors
diffs = [
    {"index": index, "source": source_rows[index] if index < len(source_rows) else None,
     "native": native_rows[index] if index < len(native_rows) else None}
    for index in range(max(len(source_rows), len(native_rows)))
    if (source_rows[index] if index < len(source_rows) else None)
    != (native_rows[index] if index < len(native_rows) else None)
]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

report = {
    "schema": "lee-callback-body-exact-r17",
    "scope": "Same-source-input callback comparison for observed P1 frame-action markers only; four fields are compared. The source fixture targets frames 62/128, and the raw tape independently proves each enter/exit pair. Not full-state or full-role parity.",
    "case_id": pre["case_id"],
    "source_run_id": pre["run_id"],
    "status": "exact_0diff" if input_match and batch_ok and source_rows == native_rows else "diverged_or_invalid",
    "fields": ["source_frame", "entering", "decoded_action", "decoded_ql"],
    "source": {
        "raw": pre["source_raw"], "raw_sha256": sha(raw),
        "build": pre["source_build"], "build_sha256": sha(build_path),
        "main_swf_sha256": pre["source_output_main_sha256"],
        "lee_swf_sha256": pre["source_output_lee_sha256"],
        "fixture": pre["source_fixture"], "fixture_sha256": sha(source_fixture_path),
        "instrumentation": pre["source_instrumentation"], "instrumentation_sha256": sha(instrumentation),
        "build_status_field": build.get("status"),
        "run_id_bound_raw": pre["run_id"],
    },
    "native": {
        "fixture": pre["native_fixture"], "fixture_sha256": sha(native_fixture),
        "fixture_inputs_setup_helpers_match_source": input_match,
        "engine_log": str((RUN / "engine.log").relative_to(ROOT)),
        "engine_log_sha256": sha(RUN / "engine.log"),
        "batch_success": batch_ok,
        "script_errors": errors,
        "runtime_hashes": {path: sha(ROOT / path) for path in (
            "godot/fighter_runtime.gd", "godot/main.gd", "godot/helper_runtime.gd",
            "godot/source_callback_registry.gd", "godot/tests/lee_callback_exact_probe.gd")},
        "runner_sha256": sha(ROOT / "godot/tests/lee_callback_exact_probe.gd"),
    },
    "source_events": source_events,
    "native_events": native_events,
    "differences": diffs,
}
(HERE / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": report["status"], "source_count": len(source_rows), "native_count": len(native_rows), "differences": len(diffs), "input_match": input_match, "batch_ok": batch_ok}, ensure_ascii=False))
if report["status"] != "exact_0diff":
    raise SystemExit(1)
