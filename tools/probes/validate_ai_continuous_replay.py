"""Fail-closed validation for a Ready-checkpoint CPU replay.

This validator only accepts a replay when the original capture contains a
complete Ready->180 fight-tick window and the Godot report proves the same
checkpoint, per-actor state rows, input schedule, and replay tapes.  A runner
that reports a local segment match while skipping an original random consumer
remains unknown/different; no frame shifting or synthetic draw is allowed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


def load_events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def source_window(events: list[dict[str, Any]], horizon: int) -> dict[str, Any]:
    ready = [e for e in events if e.get("kind") == "ready"]
    done = [e for e in events if e.get("kind") == "done"]
    if len(ready) != 1 or len(done) != 1:
        raise ValueError("source must have exactly one ready and one done event")
    checkpoint = ready[0]
    if int(done[0].get("fight_tick", -1)) != horizon:
        raise ValueError("source done event does not cover requested horizon")
    lo = int(checkpoint["sequence"])
    states = [e for e in events if e.get("kind") == "state"
              and lo <= int(e.get("sequence", -1))
              and 0 <= int(e.get("fight_tick", -1)) <= horizon]
    by_tick: dict[int, list[dict[str, Any]]] = {}
    for event in states:
        by_tick.setdefault(int(event["fight_tick"]), []).append(event)
    expected_ticks = set(range(horizon + 1))
    if set(by_tick) != expected_ticks or any(len(rows) != 2 for rows in by_tick.values()):
        raise ValueError("source state window is not exactly two actors for every fight tick")
    for tick, rows in by_tick.items():
        slots = [str(row["value"]).split(",", 1)[0] for row in rows]
        if slots != ["p1", "p2"]:
            raise ValueError(f"source actor order is not p1,p2 at fight tick {tick}")
    helpers = {}
    for kind in ("helper_state", "helper_clip_state"):
        rows = [e for e in events if e.get("kind") == kind
                and int(e.get("sequence", -1)) >= lo
                and 0 <= int(e.get("fight_tick", -1)) <= horizon]
        helper_ticks = Counter(int(e["fight_tick"]) for e in rows)
        helpers[kind] = {"rows": len(rows), "ticks": sorted(helper_ticks),
                         "counts": dict(helper_ticks)}
    inputs = [e for e in events if e.get("kind") == "input_next_display"
              and int(e.get("sequence", -1)) > lo
              and 0 <= int(e.get("fight_tick", -1)) <= horizon]
    input_ticks = sorted({int(e["fight_tick"]) for e in inputs})
    random = [e for e in events if e.get("kind") == "random"]
    clocks = [e for e in events if e.get("kind") == "clock"]
    random_before = [e for e in random if int(e["sequence"]) < lo]
    random_after = [e for e in random if int(e["sequence"]) > lo]
    return {
        "ready": checkpoint,
        "done": done[0],
        "horizon": horizon,
        "state_rows": len(states),
        "state_ticks": sorted(by_tick),
        "helper_rows": helpers,
        "helper_loads": [str(e.get("value", "")).split(",")[:2] for e in events if e.get("kind") == "helper_load"],
        "input_rows": len(inputs),
        "input_ticks": input_ticks,
        "random_before_ready": len(random_before),
        "random_cursor_at_ready": max((int(str(e["value"]).split(",", 1)[0]) for e in random_before), default=0),
        "random_after_ready": len(random_after),
        "random_sites_after_ready": Counter(
            str(e["value"]).split(",", 2)[1] for e in random_after
        ),
        "clock_rows_after_ready": len([e for e in clocks if int(e["sequence"]) > lo]),
        "source_event_counts_after_ready": dict(Counter(
            str(e.get("kind")) for e in events if int(e.get("sequence", -1)) > lo
        )),
    }


def _decode_source_number(value: str) -> float:
    if not value.startswith("f:"):
        return float(value)
    _, sign, exponent, high, low = value.split(":")
    sign_i, exponent_i, high_i, low_i = map(int, (sign, exponent, high, low))
    return sign_i * math.ldexp(high_i * 2**26 + low_i, exponent_i - 52)


def _source_value(value: str) -> Any:
    if value == "undefined":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith("f:"):
        return _decode_source_number(value)
    try:
        return int(value)
    except ValueError:
        return float(value)


def _source_state_map(events: list[dict[str, Any]], ready_sequence: int,
                      horizon: int) -> dict[tuple[int, str], dict[str, Any]]:
    fields = ("frame", "x", "y", "xscale", "action", "hp", "ql", "sw",
              "touch", "touchFloor", "hits", "paused", "hstm", "hurtSkling")
    rows: dict[tuple[int, str], dict[str, Any]] = {}
    for event in events:
        if event.get("kind") != "state" or int(event.get("sequence", -1)) < ready_sequence:
            continue
        tick = int(event.get("fight_tick", -1))
        if not 0 <= tick <= horizon:
            continue
        parts = str(event["value"]).split(",")
        if len(parts) != len(fields) + 1:
            raise ValueError("source state has unexpected field count")
        row = {field: _source_value(value) for field, value in zip(fields, parts[1:])}
        row["slot"] = parts[0]
        row["display_tick"] = int(event["display_tick"])
        key = (row["display_tick"], row["slot"])
        if key in rows:
            raise ValueError(f"duplicate source state key {key}")
        rows[key] = row
    return rows


def _expected_input_transitions(events: list[dict[str, Any]], ready_sequence: int,
                                horizon: int) -> list[dict[str, Any]]:
    fields = ("right", "attack", "down", "ranged", "jump", "special", "summon")
    held = {field: False for field in fields}
    result = []
    for event in events:
        if event.get("kind") != "input_next_display" or int(event.get("sequence", -1)) <= ready_sequence:
            continue
        tick = int(event.get("fight_tick", -1))
        if not 0 <= tick <= horizon:
            continue
        values = dict(item.split("=", 1) for item in str(event["value"]).split(",") if "=" in item)
        for field in fields:
            value = values.get(field, "undefined") == "true"
            if value != held[field]:
                result.append({"display_tick": int(event["display_tick"]),
                               "field": field, "pressed": value})
            held[field] = value
    return result


def _source_helper_map(events: list[dict[str, Any]], ready_sequence: int,
                       horizon: int) -> dict[tuple[int, str], dict[str, Any]]:
    rows = {}
    fields = ("frame", "x", "y", "xscale", "attacking", "action", "hits")
    for event in events:
        if event.get("kind") != "helper_state" or int(event.get("sequence", -1)) < ready_sequence:
            continue
        tick = int(event.get("fight_tick", -1))
        if not 0 <= tick <= horizon:
            continue
        parts = str(event["value"]).split(",")
        if len(parts) != 11:
            raise ValueError("source helper state has unexpected field count")
        row = {field: _source_value(value) for field, value in zip(fields, [parts[1], parts[2], parts[3], parts[4], parts[5], parts[6], parts[7]])}
        row["slot"] = parts[0]
        row["display_tick"] = int(event["display_tick"])
        key = (row["display_tick"], row["slot"])
        if key in rows:
            raise ValueError(f"duplicate source helper key {key}")
        rows[key] = row
    return rows


def validate(source: Path, replay: Path, horizon: int, source_build: Path) -> dict[str, Any]:
    events = load_events(source)
    build = json.loads(source_build.read_text())
    intervention_flags = [name for name in ("frame_order_probe", "recovery_order_probe",
                         "schedule_probe", "recovery_walk_first", "match_flow",
                         "body_boundaries", "body_callback_observer")
                         if bool(build.get(name, build.get("configuration", {}).get(name, False)))]
    provenance_ok = (int(build.get("frames_after_ready", -1)) == horizon
                     and bool(build.get("configuration", {}).get("p2cpu"))
                     and not intervention_flags)
    window = source_window(events, horizon)
    report = json.loads(replay.read_text())
    ready_sequence = int(window["ready"]["sequence"])
    ready_tick = int(window["ready"]["display_tick"])
    source_states = _source_state_map(events, ready_sequence, horizon)
    source_keys = set(source_states)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    source_sha_ok = report.get("reference_sha256") == source_sha
    # Build the Ready list from source sequence order; dict rows retain the exact
    # decoded state fields used by all later comparisons.
    ready_rows = sorted((row for row in source_states.values()
                         if row["display_tick"] == ready_tick), key=lambda row: row["slot"])
    expected_ready = [{"slot": row["slot"], "frame": row["frame"], "display_tick": ready_tick}
                      for row in ready_rows]
    ready_ok = report.get("original_ready") == expected_ready and report.get("native_ready") == expected_ready
    checkpoint = report.get("native_checkpoint", {})
    checkpoint_actors = {str(row.get("slot")): row for row in checkpoint.get("actors", [])}
    checkpoint_fields = ("frame", "x", "y", "xscale", "action", "hp", "ql", "sw",
                         "touch", "touchFloor", "hits", "paused", "hstm", "hurtSkling")
    actor_fields_ok = (set(checkpoint_actors) == {"p1", "p2"}
                       and all({field: checkpoint_actors[slot].get(field) for field in checkpoint_fields}
                               == {field: ready_rows[i].get(field) for field in checkpoint_fields}
                               for i, slot in enumerate(("p1", "p2"))))
    checkpoint_ok = (ready_ok and int(checkpoint.get("display_tick", -1)) == ready_tick
                     and int(checkpoint.get("fight_tick", -1)) == 0
                     and actor_fields_ok
                     and sorted(str(helper.get("helper_id", "")) for helper in checkpoint.get("helpers", []))
                     == sorted(str(row[1]) for row in window["helper_loads"])
                     and all(not bool(helper.get("attacking")) and int(helper.get("deferred_frame", -1)) == -1
                             for helper in checkpoint.get("helpers", []))
                     and checkpoint.get("battle_intro_active") is False
                     and checkpoint.get("pending_frame_actions") == [0, 0])
    expected_keys = sorted(source_keys)
    frame_rows = [row for row in report.get("frame_comparisons", [])
                  if int(row.get("display_tick", -1)) in {key[0] for key in expected_keys}]
    frame_map = {int(row.get("display_tick", -1)): row for row in frame_rows}
    expected_frame_map = {}
    for (display_tick, _slot), row in source_states.items():
        expected_frame_map.setdefault(display_tick, []).append(row["frame"])
    expected_frame_map = {tick: [rows[0]["frame"], rows[1]["frame"]]
                          for tick, rows in ((tick, sorted((r for (d, _), r in source_states.items() if d == tick),
                                                            key=lambda r: r["slot"]))
                                             for tick in {key[0] for key in expected_keys})}
    frame_ok = (set(frame_map) == set(expected_frame_map)
                and len(frame_rows) == len(expected_frame_map)
                and all(frame_map[tick].get("actual") == expected_frame_map[tick]
                        and frame_map[tick].get("expected") == expected_frame_map[tick]
                        for tick in expected_frame_map))
    state_rows = [row for row in report.get("state_comparisons", [])
                  if int(row.get("display_tick", -1)) in {key[0] for key in expected_keys}]
    state_map = {(int(row.get("display_tick", -1)), str(row.get("slot"))): row for row in state_rows}
    state_ok = (set(state_map) == source_keys and len(state_rows) == len(source_states)
                and all(state_map[key].get("actual") == {field: source_states[key][field]
                                                            for field in ("action", "hp", "ql", "sw", "touch", "touchFloor", "hits", "paused", "hstm", "hurtSkling")}
                        for key in source_keys))
    geometry_rows = [row for row in report.get("geometry_comparisons", [])
                     if int(row.get("display_tick", -1)) in {key[0] for key in expected_keys}]
    geometry_map = {(int(row.get("display_tick", -1)), str(row.get("slot"))): row for row in geometry_rows}
    geometry_ok = (set(geometry_map) == source_keys and len(geometry_rows) == len(source_states)
                   and all(geometry_map[key].get("actual") == {field: source_states[key][field]
                                                                 for field in ("x", "y", "xscale")}
                           for key in source_keys))
    source_helpers = _source_helper_map(events, ready_sequence, horizon)
    native_helpers = report.get("helper_snapshots", [])
    helper_map = {(int(row.get("display_tick", -1)), str(row.get("slot"))): row
                  for row in native_helpers}
    helper_ok = (set(helper_map) == set(source_helpers) and len(native_helpers) == len(source_helpers)
                 and all(helper_map[key].get("frame") == source_helpers[key]["frame"]
                         and math.isclose(float(helper_map[key].get("x")), float(source_helpers[key]["x"]), rel_tol=0.0, abs_tol=0.0)
                         and math.isclose(float(helper_map[key].get("y")), float(source_helpers[key]["y"]), rel_tol=0.0, abs_tol=0.0)
                         and helper_map[key].get("facing", 0) * 100 == source_helpers[key]["xscale"]
                         and helper_map[key].get("attacking") == source_helpers[key]["attacking"]
                         and helper_map[key].get("action") == source_helpers[key]["action"]
                         and (helper_map[key].get("hits") == source_helpers[key]["hits"]
                              or (source_helpers[key]["hits"] is None and helper_map[key].get("hits") == 0))
                         for key in source_helpers))
    expected_inputs = _expected_input_transitions(events, ready_sequence, horizon)
    input_ok = report.get("input_transitions") == expected_inputs
    # The continuous runner starts at the first source-accepted intro poll. Its
    # tape's original-index slice is therefore explicit and must be complete.
    true_polls = [e for e in events if e.get("kind") == "intro_poll_state"
                  and str(e.get("value", "")).split(",")[1:2] == ["true"]]
    replay_start = min((int(e["sequence"]) for e in true_polls), default=-1)
    expected_random = []
    for event in events:
        if event.get("kind") != "random" or int(event.get("sequence", -1)) <= replay_start:
            continue
        parts = str(event["value"]).split(",", 2)
        expected_random.append((int(parts[0]), parts[1], _decode_source_number(parts[2])))
    consumed_rows = report.get("random_consumed", [])
    actual_indices = [int(value) for value in report.get("random_original_indices", [])]
    random_ok = bool(report.get("random_tape_complete")) and not report.get("random_failure")
    random_sequence_ok = (actual_indices == [record[0] for record in expected_random]
                          and [str(value.get("site", "")) for value in consumed_rows]
                          == [record[1] for record in expected_random]
                          and all(math.isclose(float(value.get("value")), record[2], rel_tol=0.0, abs_tol=0.0)
                                  for value, record in zip(consumed_rows, expected_random)))
    cursor_offset = actual_indices[0] - 1 if actual_indices else -1
    expected_local_cursor = int(window["random_cursor_at_ready"]) - cursor_offset if cursor_offset >= 0 else -1
    random_cursor_ok = int(checkpoint.get("random_absolute_index", -1)) == expected_local_cursor
    random_scope_ok = random_sequence_ok and random_cursor_ok
    expected_clock = []
    for event in events:
        if event.get("kind") != "clock" or int(event.get("sequence", -1)) <= ready_sequence:
            continue
        index, site, value = str(event["value"]).split(",")
        expected_clock.append({"site": site, "value": int(value), "original_index": int(index)})
    clock_ok = bool(report.get("clock_tape_complete")) and report.get("clock_consumed") == expected_clock
    status = "validated" if all((frame_ok, state_ok, geometry_ok, helper_ok, checkpoint_ok, source_sha_ok,
                                  provenance_ok, random_ok, random_scope_ok, input_ok, clock_ok)) else "unknown"
    first_reason = None
    for condition, reason in ((not source_sha_ok, "source_capture_hash_mismatch"),
                              (not provenance_ok, "source_build_provenance_not_clean"),
                              (not checkpoint_ok, "ready_checkpoint_restore_incomplete"),
                              (not frame_ok, "source_recomputed_frame_coverage_mismatch"),
                              (not state_ok, "source_recomputed_state_coverage_mismatch"),
                              (not geometry_ok, "source_recomputed_geometry_coverage_mismatch"),
                              (not helper_ok, "source_recomputed_helper_coverage_or_field_mismatch"),
                              (not input_ok, "source_recomputed_input_consumption_mismatch"),
                              (not random_ok, "random_tape_incomplete"),
                              (not random_sequence_ok, "random_original_slice_mismatch"),
                              (not random_cursor_ok, "ready_random_cursor_mismatch"),
                              (not clock_ok, "clock_tape_mismatch")):
        if condition:
            first_reason = reason
            break
    return {
        "format": "ai-continuous-replay-acceptance-v1", "status": status,
        "acceptance_status": status, "source": str(source), "replay": str(replay),
        "source_build": str(source_build),
        "source_build_provenance": {"clean": provenance_ok, "intervention_flags": intervention_flags},
        "checkpoint": window["ready"], "horizon": horizon,
        "source_window": window,
        "checks": {
            "ready_checkpoint": checkpoint_ok,
            "source_capture_sha256": {"expected": source_sha, "actual": report.get("reference_sha256"), "matched": source_sha_ok},
            "post_ready_frames": {"expected": len(expected_frame_map), "actual": len(frame_rows), "matched": frame_ok},
            "post_ready_states": {"expected": len(source_states), "actual": len(state_rows), "matched": state_ok},
            "post_ready_geometry": {"expected": len(source_states), "actual": len(geometry_rows), "matched": geometry_ok},
            "post_ready_helpers": {"expected": len(source_helpers), "actual": len(native_helpers), "matched": helper_ok,
                                    "fields": ["frame", "x", "y", "xscale/facing", "attacking", "action", "hits"]},
            "input_transitions": {"expected": expected_inputs, "actual": report.get("input_transitions"), "matched": input_ok},
            "random_consumers": {"replay_start_sequence": replay_start, "expected_original_indices": [r[0] for r in expected_random],
                                  "replay_original_indices": actual_indices, "local_cursor_offset": cursor_offset,
                                  "expected_local_cursor_at_ready": expected_local_cursor,
                                  "replay_local_cursor_at_ready": checkpoint.get("random_absolute_index"),
                                  "sequence_match": random_sequence_ok, "scope_complete": random_scope_ok, "replay_consumed": len(consumed_rows)},
            "clock": {"expected": expected_clock, "actual": report.get("clock_consumed"), "matched": clock_ok},
        },
        "first_reason": first_reason, "replay_status": report.get("status"),
        "limits": ["Ready checkpoint scope excludes boot/load/intro parity.",
                   "Only source-observed events are accepted; no frame shifting or synthetic draw is allowed.",
                   "Validated result covers this selected 180-tick CPU replay, not all AI inputs or full parity."],
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--horizon", type=int, default=180)
    parser.add_argument("--source-build", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_build = args.source_build or args.source.parent / "build.json"
    if not source_build.exists():
        parser.error(f"source build metadata not found: {source_build}")
    result = validate(args.source, args.replay, args.horizon, source_build)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "first_reason": result["first_reason"],
                      "source_states": result["source_window"]["state_rows"],
                      "replay_consumed": result["checks"]["random_consumers"]["replay_consumed"]}))
    return 0 if result["status"] == "validated" else 1


if __name__ == "__main__":
    raise SystemExit(main())
