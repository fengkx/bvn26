#!/usr/bin/env python3
"""Audit existing Lee source callback captures against the callback-only Godot batch."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "evidence/characters/lee/godot/callback-exact-r15"))
from event_tape import parse_event_line
sys.path.insert(0, str(ROOT / "tools/probes"))
from collect_ai_reference import decode_number

LOG = HERE / "engine.log"
BUNDLE = ROOT / "evidence/characters/lee/callback-exact-r01/source-callback-provenance-r01"
CASES = [
    {"name": "recovery-p2-hp1", "native_fixture": "recovery-p2-hp1.fixture.json",
     "native_id": "lee-recovery-p2-hp1-r01", "slot": "p2", "frames": [8, 1219, 1083]},
    {"name": "kill700-external-tape", "native_fixture": "kill700-external-tape.fixture.json",
     "native_id": "lee-kill700-external-tape-r02", "slot": "p1", "frames": [8, 1219, 1260]},
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_native_summaries() -> dict[str, list[dict]]:
    found = {}
    for line in LOG.read_text().splitlines():
        if line.startswith("LEE_EXACT_CALLBACK_SUMMARY "):
            item = json.loads(line.split(" ", 1)[1])
            found[item["fixture"]] = item["events"]
    return found


def first_source_states(raw: Path, run_id: str) -> tuple[dict, list[dict]]:
    preconditions = []
    ready = None
    states = {}
    for line in raw.read_text().splitlines():
        if not line.strip():
            continue
        event = parse_event_line(line)
        if event["run_id"] != run_id:
            continue
        if event["kind"] == "source_state_precondition":
            preconditions.append({"sequence": event["sequence"], "display_tick": event["display_tick"],
                                  "fight_tick": event["fight_tick"], "value": event["value"]})
        if event["kind"] == "ready" and ready is None:
            ready = event
        if event["kind"] == "state" and event["fight_tick"] == 0:
            fields = event["value"].split(",")
            if fields[0] not in states:
                states[fields[0]] = {
                    "slot": fields[0], "sequence": event["sequence"],
                    "display_tick": event["display_tick"], "fight_tick": event["fight_tick"],
                    "frame": int(fields[1]), "hp": float(decode_number(fields[6])),
                    "ql": float(decode_number(fields[7])),
                }
    return {"ready": None if ready is None else {
        "sequence": ready["sequence"], "display_tick": ready["display_tick"],
        "fight_tick": ready["fight_tick"]}, "states": states}, preconditions


def source_callbacks(raw: Path, run_id: str, slot: str, frames: list[int]) -> list[dict]:
    events = []
    for line in raw.read_text().splitlines():
        if not line.strip():
            continue
        event = parse_event_line(line)
        if event["run_id"] != run_id or event["kind"] != "body_boundary":
            continue
        fields = event["value"].split(",")
        if len(fields) < 7 or fields[0] != slot or int(fields[1]) not in frames:
            continue
        events.append({"slot": slot, "source_frame": int(fields[1]),
                       "entering": fields[2] == "true", "current_frame": int(fields[3]),
                       "action": float(decode_number(fields[4])), "ql": float(decode_number(fields[6])),
                       "sequence": event["sequence"], "fight_tick": event["fight_tick"],
                       "display_tick": event["display_tick"]})
    return events


native_summaries = get_native_summaries()
report = {
    "schema": "lee-callback-exact-body-final-r01",
    "scope": "Existing source builds/raws paired to one headless callback-probe batch; no production changes.",
    "batch": {"log": str(LOG.relative_to(ROOT)), "log_sha256": sha(LOG),
              "batch_ok": "MOVE_CASE_BATCH_OK 2" in LOG.read_text(),
              "script_errors": [line for line in LOG.read_text().splitlines() if "SCRIPT ERROR" in line],
              "probe_sha256": sha(ROOT / "godot/tests/lee_callback_exact_probe.gd"),
              "main_sha256": sha(ROOT / "godot/main.gd"),
              "fighter_runtime_sha256": sha(ROOT / "godot/fighter_runtime.gd"),
              "source_callback_registry_sha256": sha(ROOT / "godot/source_callback_registry.gd"),
              "runtime_hashes": {path: sha(ROOT / path) for path in (
                  "godot/main.gd", "godot/fighter_runtime.gd", "godot/helper_runtime.gd",
                  "godot/source_callback_registry.gd",
                  "godot/generated/fighters/lee/player_controller/controller.gd",
                  "godot/generated/fighters/lee/ai_controller/controller.gd",
                  "godot/generated/main/execution_profile.json",
              )}},
    "cases": [],
}
for spec in CASES:
    provenance_path = BUNDLE / spec["name"] / "provenance.json"
    provenance = json.loads(provenance_path.read_text())
    source_raw = ROOT / provenance["raw_events_path"]
    source_build_path = ROOT / provenance["build_path"]
    source_build = json.loads(source_build_path.read_text())
    source_fixture_path = ROOT / provenance["fixture_path"]
    source_fixture = json.loads(source_fixture_path.read_text())
    native_fixture_path = HERE / spec["native_fixture"]
    native_fixture = json.loads(native_fixture_path.read_text())
    native_out = HERE / "out" / f"{spec['native_id']}.json"
    native_interventions = HERE / "out" / f"{spec['native_id']}.json.interventions.json"
    source_initial, preconditions = first_source_states(source_raw, source_build["run_id"])
    native_rows = json.loads(native_out.read_text())
    native_initial = {row["slot"]: {"slot": row["slot"], "tick": row["tick"], "frame": row["frame"],
                                     "hp": row["hp"], "ql": row["ql"]}
                      for row in native_rows if row["tick"] == 0}
    native_events = [event for event in native_summaries.get(spec["native_id"], [])
                     if event["slot"] == spec["slot"] and event["source_frame"] in spec["frames"]]
    src_events = source_callbacks(source_raw, source_build["run_id"], spec["slot"], spec["frames"])
    per_frame = {}
    for frame in spec["frames"]:
        src = [event for event in src_events if event["source_frame"] == frame]
        nat = [event for event in native_events if event["source_frame"] == frame]
        src_cmp = [{key: event[key] for key in ("source_frame", "entering", "action", "ql")} for event in src]
        nat_cmp = [{key: event[key] for key in ("source_frame", "entering", "action", "ql")} for event in nat]
        per_frame[str(frame)] = {
            "source_event_count": len(src), "native_event_count": len(nat),
            "four_fields_sequence_equal": src_cmp == nat_cmp,
            "current_frame_source": [event["current_frame"] for event in src],
            "current_frame_native": [event["current_frame"] for event in nat],
            "source_events": src, "native_events": nat,
        }
    source_move = source_build["move_case"]
    matching_config = all(native_fixture.get(key) == source_move.get(key)
                          for key in ("fighters", "setup", "inputs", "p1_helper", "p2_helper"))
    expected_state = {slot: state["hp"] for slot, state in source_initial["states"].items()}
    observed_state = {slot: state["hp"] for slot, state in native_initial.items()}
    initial_health_match = expected_state == observed_state
    if not initial_health_match:
        status = "invalid_same_input_source_initial_state_mismatch"
    elif all(per_frame[str(frame)]["four_fields_sequence_equal"] for frame in spec["frames"]):
        status = "exact_callback_sequence_match"
    else:
        status = "callback_sequence_different"
    report["cases"].append({
        "case_id": spec["name"], "status": status, "slot": spec["slot"],
        "target_frames": spec["frames"], "configuration_fields_match": matching_config,
        "source_initial": source_initial, "source_precondition_events": preconditions,
        "native_initial": native_initial, "initial_health_match": initial_health_match,
        "native_interventions": json.loads(native_interventions.read_text()),
        "source": {"run_id": source_build["run_id"], "raw": str(source_raw.relative_to(ROOT)),
                   "raw_sha256": sha(source_raw), "build": str(source_build_path.relative_to(ROOT)),
                   "build_sha256": sha(source_build_path), "fixture": str(source_fixture_path.relative_to(ROOT)),
                   "fixture_sha256": sha(source_fixture_path), "instrumentation_sha256": sha(ROOT / provenance["instrumentation_path"]),
                   "fixture_from_build": source_fixture},
        "native": {"fixture": str(native_fixture_path.relative_to(ROOT)),
                   "fixture_sha256": sha(native_fixture_path), "output": str(native_out.relative_to(ROOT)),
                   "output_sha256": sha(native_out), "interventions": str(native_interventions.relative_to(ROOT)),
                   "native_event_count": len(native_events)},
        "fields": ["source_frame", "entering", "action", "ql"],
        "frames": per_frame,
    })
report["summary"] = {
    "source_cases": len(report["cases"]),
    "same_input_cases": sum(case["configuration_fields_match"] and case["initial_health_match"] for case in report["cases"]),
    "invalid_initial_state_cases": sum(case["status"] == "invalid_same_input_source_initial_state_mismatch" for case in report["cases"]),
    "frames_with_exact_four_field_sequences": sum(frame["four_fields_sequence_equal"] for case in report["cases"] for frame in case["frames"].values()),
    "frames_with_different_sequences": sum(not frame["four_fields_sequence_equal"] for case in report["cases"] for frame in case["frames"].values()),
}
(HERE / "comparison-r01.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report["summary"], ensure_ascii=False))
