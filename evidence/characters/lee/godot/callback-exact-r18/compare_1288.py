#!/usr/bin/env python3
"""Compare the natural P1 frame-1288 callback to its exact source fixture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
pre = json.loads((HERE / "preflight.json").read_text())
source_raw = ROOT / pre["source_raw"]
source_build_path = ROOT / pre["source_build"]
source_fixture_path = ROOT / pre["source_fixture"]
native_fixture_path = ROOT / pre["native_fixture"]
native_log = HERE / "engine-r03.log"
native_out = HERE / "out-run-r03/round-loss-failure-1288-r06.json"
sys.path.insert(0, str(ROOT / "evidence/characters/lee/godot/callback-exact-r15"))
from event_tape import parse_event_line
sys.path.insert(0, str(ROOT / "tools/probes"))
from collect_ai_reference import decode_number


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


build = json.loads(source_build_path.read_text())
source_fixture = json.loads(source_fixture_path.read_text())
native_fixture = json.loads(native_fixture_path.read_text())
source_rows = []
for line in source_raw.read_text().splitlines():
    if not line.strip():
        continue
    event = parse_event_line(line)
    if event["run_id"] != pre["run_id"] or event["kind"] != "body_boundary":
        continue
    fields = event["value"].split(",")
    if len(fields) < 7 or fields[0] != "p1" or fields[1] != "1288":
        continue
    source_rows.append({
        "slot": fields[0], "source_frame": int(fields[1]), "entering": fields[2] == "true",
        "current_frame": int(fields[3]), "action": float(decode_number(fields[4])),
        "hp": float(decode_number(fields[5])), "ql": float(decode_number(fields[6])),
        "sequence": event["sequence"], "fight_tick": event["fight_tick"],
        "display_tick": event["display_tick"], "time_ms": event["time_ms"],
    })
native_rows = []
lines = native_log.read_text().splitlines()
for line in lines:
    if not line.startswith("LEE_EXACT_CALLBACK "):
        continue
    event = json.loads(line.split(" ", 1)[1])
    if event["slot"] == "p1" and event["source_frame"] == 1288:
        native_rows.append({key: event[key] for key in (
            "slot", "source_frame", "entering", "current_frame", "action", "ql", "fixture_tick", "tick")})
summary = next((json.loads(line.split(" ", 1)[1]) for line in lines
                if line.startswith("LEE_EXACT_CALLBACK_SUMMARY ")), None)
errors = [line for line in lines if "SCRIPT ERROR" in line]
source_fields = [{key: row[key] for key in ("source_frame", "entering", "action", "ql")} for row in source_rows]
native_fields = [{key: row[key] for key in ("source_frame", "entering", "action", "ql")} for row in native_rows]
move = build["move_case"]
input_match = all(native_fixture.get(key) == move.get(key) for key in (
    "fighter", "slot", "label", "scenario", "frames", "setup", "inputs", "has_source_timeline",
    "source_dispatch", "fighters", "p1_helper", "p2_helper"))
source_events_countdown = 0
native_countdown = []
progress = []
for line in lines:
    if line.startswith("LEE_REAL_COUNTDOWN_TIMER_FIRE "):
        native_countdown.append(json.loads(line.split(" ", 1)[1]))
    elif line.startswith("LEE_REAL_CLOCK_PROGRESS "):
        progress.append(json.loads(line.split(" ", 1)[1]))

result = {
    "schema": "lee-callback-1288-natural-callback-r01",
    "status": "exact_0diff" if input_match and source_fields == native_fields and not errors and summary else "diverged_or_invalid",
    "scope": "Natural same-source-input frame-action callback pair only. Four accepted fields are source_frame, entering, decoded action and decoded ql. Real Timer and round lifecycle are diagnostic; this does not claim full timer, match lifecycle, state or role parity.",
    "source": {
        "run_id": pre["run_id"], "raw": pre["source_raw"], "raw_sha256": sha(source_raw),
        "build": pre["source_build"], "build_sha256": sha(source_build_path),
        "fixture": pre["source_fixture"], "fixture_sha256": sha(source_fixture_path),
        "instrumentation": pre["source_instrumentation"],
        "instrumentation_sha256": sha(ROOT / pre["source_instrumentation"]),
        "main_swf_sha256": pre["source_outputs_sha256"]["game/main.swf"],
        "lee_swf_sha256": pre["source_outputs_sha256"]["game/fighter/lee.swf"],
        "source_configuration": pre["source_configuration"],
        "source_move_case": move, "rows": source_rows,
    },
    "native": {
        "fixture": pre["native_fixture"], "fixture_sha256": sha(native_fixture_path),
        "output": str(native_out.relative_to(ROOT)), "output_sha256": sha(native_out),
        "engine_log": str(native_log.relative_to(ROOT)), "engine_log_sha256": sha(native_log),
        "probe_sha256": sha(ROOT / "godot/tests/lee_callback_exact_probe.gd"),
        "runtime_hashes": {path: sha(ROOT / path) for path in (
            "godot/fighter_runtime.gd", "godot/main.gd", "godot/helper_runtime.gd",
            "godot/source_callback_registry.gd", "godot/generated/main/execution_profile.json")},
        "fixture_inputs_setup_helpers_match_source": input_match,
        "rows": native_rows,
        "script_errors": errors,
        "terminal": next((json.loads(line.split(" ", 1)[1]) for line in lines
                          if line.startswith("LEE_FIXTURE_TERMINAL ")), None),
    },
    "fields": ["source_frame", "entering", "action", "ql"],
    "source_comparison": source_fields,
    "native_comparison": native_fields,
    "timing_diagnostic": {
        "source_target_fight_tick": source_rows[0]["fight_tick"] if source_rows else None,
        "source_target_time_ms": source_rows[0]["time_ms"] if source_rows else None,
        "native_target_fixture_tick": native_rows[0]["fixture_tick"] if native_rows else None,
        "native_target_physics_tick": native_rows[0]["tick"] if native_rows else None,
        "native_real_clock_progress": progress,
        "native_countdown_timeout_event_count": len(native_countdown),
        "native_countdown_last_events": native_countdown[-6:],
        "timing_match": False,
        "timing_note": "The source and native fixture clocks are not mapped by this bounded callback check; observed fight_tick 2263 and fixture_tick 2228 differ by 35. Lee is separately auditing the timer/Ready cause.",
    },
}
(HERE / "comparison-r01.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": result["status"], "source": source_fields, "native": native_fields,
                  "input_match": input_match, "timer_events": len(native_countdown),
                  "script_errors": errors}, ensure_ascii=False))
