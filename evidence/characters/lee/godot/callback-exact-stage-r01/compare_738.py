#!/usr/bin/env python3
"""Strict four-field comparison for the real rooftop 738 callback fixture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "evidence/characters/lee/original/lee-callback-738-rooftop-walkoff-r04"
NATIVE_FIXTURE = HERE / "lee-callback-738-rooftop-walkoff-r04.native-fixture-r02.json"
NATIVE_LOG = HERE / "engine-r02.log"
NATIVE_OUT = HERE / "out/lee-callback-738-rooftop-walkoff-r04-r02.json"
sys.path.insert(0, str(ROOT / "evidence/characters/lee/godot/callback-exact-r15"))
from event_tape import parse_event_line
sys.path.insert(0, str(ROOT / "tools/probes"))
from collect_ai_reference import decode_number


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


build_path = SOURCE_DIR / "build.json"
source_fixture_path = SOURCE_DIR / "fixture.json"
raw_path = SOURCE_DIR / "events.jsonl"
instrumentation_path = SOURCE_DIR / "instrumentation.diff"
overlay_path = SOURCE_DIR / "stage-build-overlay.diff"
build = json.loads(build_path.read_text())
move = build["move_case"]
source_fixture = json.loads(source_fixture_path.read_text())
native_fixture = json.loads(NATIVE_FIXTURE.read_text())
provenance = json.loads((HERE / "provenance.json").read_text())

source_rows = []
for line in raw_path.read_text().splitlines():
    if not line.strip():
        continue
    event = parse_event_line(line)
    if event["run_id"] != build["run_id"] or event["kind"] != "body_boundary":
        continue
    fields = event["value"].split(",")
    if len(fields) < 7 or fields[0] != "p1" or fields[1] != "738":
        continue
    source_rows.append({
        "slot": fields[0], "source_frame": int(fields[1]), "entering": fields[2] == "true",
        "current_frame": int(fields[3]), "action": float(decode_number(fields[4])),
        "ql": float(decode_number(fields[6])), "sequence": event["sequence"],
        "fight_tick": event["fight_tick"], "display_tick": event["display_tick"],
    })
native_rows = []
for line in NATIVE_LOG.read_text().splitlines():
    if not line.startswith("LEE_EXACT_CALLBACK "):
        continue
    event = json.loads(line.split(" ", 1)[1])
    if event["slot"] == "p1" and event["source_frame"] == 738:
        native_rows.append({key: event[key] for key in (
            "slot", "source_frame", "entering", "current_frame", "action", "ql", "fixture_tick", "tick")})

source_compared = [{key: row[key] for key in ("source_frame", "entering", "action", "ql")} for row in source_rows]
native_compared = [{key: row[key] for key in ("source_frame", "entering", "action", "ql")} for row in native_rows]
source_inputs = {
    "fighter": move["fighter"], "slot": move["slot"], "label": move["label"], "frames": move["frames"],
    "setup": move["setup"], "inputs": move["inputs"], "fighters": move["fighters"],
    "p1_helper": move["p1_helper"], "p2_helper": move["p2_helper"], "stage": build["configuration"]["stage"],
}
native_inputs = {key: native_fixture.get(key) for key in source_inputs}
input_match = source_inputs == native_inputs
sequence_match = source_compared == native_compared
summary = next((json.loads(line.split(" ", 1)[1]) for line in NATIVE_LOG.read_text().splitlines()
                if line.startswith("LEE_EXACT_CALLBACK_SUMMARY ")), None)
script_errors = [line for line in NATIVE_LOG.read_text().splitlines() if "SCRIPT ERROR" in line]
result = {
    "schema": "lee-callback-738-rooftop-four-field-r01",
    "status": "exact_0diff" if input_match and sequence_match and not script_errors and summary is not None else "diverged_or_invalid",
    "scope": "Same-build, same-input, P1 frame-action callback comparison on the original rooftop stage. Only source_frame, entering, action and decoded ql are accepted; no full-state, visual or clock parity is claimed.",
    "source": {
        "run_id": build["run_id"], "raw": str(raw_path.relative_to(ROOT)), "raw_sha256": sha(raw_path),
        "build": str(build_path.relative_to(ROOT)), "build_sha256": sha(build_path),
        "fixture": str(source_fixture_path.relative_to(ROOT)), "fixture_sha256": sha(source_fixture_path),
        "instrumentation": str(instrumentation_path.relative_to(ROOT)), "instrumentation_sha256": sha(instrumentation_path),
        "stage_overlay": str(overlay_path.relative_to(ROOT)), "stage_overlay_sha256": sha(overlay_path),
        "main_swf_sha256": build["outputs_sha256"]["game/main.swf"],
        "lee_swf_sha256": build["outputs_sha256"]["game/fighter/lee.swf"],
        "rows": source_rows,
    },
    "native": {
        "fixture": str(NATIVE_FIXTURE.relative_to(ROOT)), "fixture_sha256": sha(NATIVE_FIXTURE),
        "engine_log": str(NATIVE_LOG.relative_to(ROOT)), "engine_log_sha256": sha(NATIVE_LOG),
        "output": str(NATIVE_OUT.relative_to(ROOT)), "output_sha256": sha(NATIVE_OUT),
        "probe_sha256": sha(ROOT / "godot/tests/lee_callback_exact_probe.gd"),
        "move_case_runner_sha256": sha(ROOT / "godot/tests/move_case_reference.gd"),
        "runtime_hashes": {path: sha(ROOT / path) for path in (
            "godot/fighter_runtime.gd", "godot/main.gd", "godot/helper_runtime.gd",
            "godot/source_callback_registry.gd", "godot/generated/main/execution_profile.json")},
        "stage_preflight": provenance,
        "rows": native_rows,
        "script_errors": script_errors,
    },
    "fixture_inputs_setup_helpers_stage_match": input_match,
    "fields": ["source_frame", "entering", "action", "ql"],
    "source_comparison": source_compared,
    "native_comparison": native_compared,
    "clock_comparison": "not performed; source fight_tick 109 and native fixture_tick 110 are retained as separate clocks",
}
(HERE / "comparison-r01.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": result["status"], "source_rows": len(source_rows), "native_rows": len(native_rows),
                  "input_match": input_match, "script_errors": script_errors}, ensure_ascii=False))
