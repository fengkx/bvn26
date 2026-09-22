#!/usr/bin/env python3
"""Derive strict same-build four-field results for the completed Lee body batch."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
PROV = ROOT / "evidence/characters/lee/callback-exact-r01/source-callback-provenance-r01/kill700-external-tape"
SOURCE_RAW = ROOT / "evidence/characters/lee/original/lee-body-boundaries-r02/events.jsonl"
SOURCE_BUILD = PROV / "build.json"
SOURCE_FIXTURE = PROV / "fixture-from-build.json"
SOURCE_PROVENANCE = PROV / "provenance.json"
NATIVE_FIXTURE = HERE / "kill700-external-tape.fixture.json"
NATIVE_OUT = HERE / "out/lee-kill700-external-tape-r02.json"
ENGINE_LOG = HERE / "engine.log"
sys.path.insert(0, str(ROOT / "evidence/characters/lee/godot/callback-exact-r15"))
from event_tape import parse_event_line
sys.path.insert(0, str(ROOT / "tools/probes"))
from collect_ai_reference import decode_number


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


build = json.loads(SOURCE_BUILD.read_text())
source_fixture = json.loads(SOURCE_FIXTURE.read_text())
provenance = json.loads(SOURCE_PROVENANCE.read_text())
native_fixture = json.loads(NATIVE_FIXTURE.read_text())
run_id = str(build["run_id"])
move = build["move_case"]
targets = {1219: "p1", 1260: "p1"}
source_rows = {frame: [] for frame in targets}
for line in SOURCE_RAW.read_text().splitlines():
    if not line.strip():
        continue
    event = parse_event_line(line)
    if event["run_id"] != run_id or event["kind"] != "body_boundary":
        continue
    fields = event["value"].split(",")
    if len(fields) < 7:
        continue
    frame = int(fields[1]) if fields[1].isdigit() else -1
    if frame not in targets or fields[0] != targets[frame]:
        continue
    source_rows[frame].append({
        "slot": fields[0], "source_frame": frame, "entering": fields[2] == "true",
        "current_frame": int(fields[3]), "action": float(decode_number(fields[4])),
        "ql": float(decode_number(fields[6])), "sequence": event["sequence"],
        "fight_tick": event["fight_tick"], "display_tick": event["display_tick"],
    })

log_lines = ENGINE_LOG.read_text().splitlines()
summary = next((json.loads(line.split(" ", 1)[1]) for line in log_lines
                if line.startswith("LEE_EXACT_CALLBACK_SUMMARY ")
                and json.loads(line.split(" ", 1)[1]).get("fixture") == native_fixture["id"]), None)
script_errors = [line for line in log_lines if "SCRIPT ERROR" in line]
native_all = summary["events"] if summary is not None else []
native_rows = {frame: [row for row in native_all if row["slot"] == targets[frame] and row["source_frame"] == frame]
               for frame in targets}

input_keys = ("fighter", "slot", "label", "scenario", "frames", "setup", "inputs",
              "has_source_timeline", "source_dispatch", "fighters", "p1_helper", "p2_helper")
input_match = all(native_fixture.get(key) == move.get(key) for key in input_keys)
results = []
for frame, slot in targets.items():
    source_compared = [{key: row[key] for key in ("source_frame", "entering", "action", "ql")}
                       for row in source_rows[frame]]
    native_compared = [{key: row[key] for key in ("source_frame", "entering", "action", "ql")}
                       for row in native_rows[frame]]
    results.append({
        "source_frame": frame, "slot": slot,
        "status": "exact_0diff" if input_match and source_compared == native_compared and source_compared else "diverged_or_invalid",
        "fields": ["source_frame", "entering", "action", "ql"],
        "source_rows": source_rows[frame], "native_rows": native_rows[frame],
        "source_comparison": source_compared, "native_comparison": native_compared,
        "difference_count": sum(a != b for a, b in zip(source_compared, native_compared))
            + abs(len(source_compared) - len(native_compared)),
    })

report = {
    "schema": "lee-callback-body-final-r01",
    "scope": "Same source build/input and native fixture. Only each requested frame's source_frame, enter/exit, decoded action and ql are compared. This is not full-state or full-role parity.",
    "source": {
        "run_id": run_id, "raw": str(SOURCE_RAW.relative_to(ROOT)), "raw_sha256": sha(SOURCE_RAW),
        "build": str(SOURCE_BUILD.relative_to(ROOT)), "build_sha256": sha(SOURCE_BUILD),
        "fixture": str(SOURCE_FIXTURE.relative_to(ROOT)), "fixture_sha256": sha(SOURCE_FIXTURE),
        "provenance": str(SOURCE_PROVENANCE.relative_to(ROOT)), "provenance_sha256": sha(SOURCE_PROVENANCE),
        "capture_url_actual_swfs": provenance["actual_swfs_on_capture_url"],
        "capture_hash_limit": provenance.get("runtime_hash_limit"),
        "move_case": move,
    },
    "native": {
        "fixture": str(NATIVE_FIXTURE.relative_to(ROOT)), "fixture_sha256": sha(NATIVE_FIXTURE),
        "output": str(NATIVE_OUT.relative_to(ROOT)), "output_sha256": sha(NATIVE_OUT),
        "engine_log": str(ENGINE_LOG.relative_to(ROOT)), "engine_log_sha256": sha(ENGINE_LOG),
        "probe_sha256": sha(ROOT / "godot/tests/lee_callback_exact_probe.gd"),
        "runtime_hashes": {path: sha(ROOT / path) for path in (
            "godot/fighter_runtime.gd", "godot/main.gd", "godot/helper_runtime.gd",
            "godot/source_callback_registry.gd", "godot/generated/main/execution_profile.json")},
        "fixture_inputs_setup_helpers_match_source": input_match,
        "script_errors": script_errors,
    },
    "results": results,
}
(HERE / "comparison-r01.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"input_match": input_match, "results": [
    {"frame": row["source_frame"], "slot": row["slot"], "status": row["status"],
     "source_count": len(row["source_rows"]), "native_count": len(row["native_rows"]),
     "differences": row["difference_count"]} for row in results], "script_errors": script_errors}, ensure_ascii=False))
