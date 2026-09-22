#!/usr/bin/env python3
"""Strict same-source-input comparison for two Lee clip callbacks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
RUN = HERE / (sys.argv[1] if len(sys.argv) > 1 else "retry-01")
sys.path.insert(0, str(HERE.parent / "callback-exact-r15"))
from event_tape import parse_event_line


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_clip_rows(case: dict) -> tuple[list[dict], dict]:
    raw = ROOT / case["source_raw"]
    rows = []
    actor_state = {}
    wanted = {target["source_path"]: target for target in case["targets"]}
    for line in raw.read_text().splitlines():
        if not line.strip():
            continue
        try:
            event = parse_event_line(line)
        except ValueError as exc:
            raise SystemExit(f"invalid source event in {raw}: {exc}") from exc
        if event["run_id"] != case["run_id"]:
            continue
        if event["kind"] == "state":
            values = event["value"].split(",")
            if len(values) >= 2 and values[0] in ("p1", "p2"):
                actor_state[(event["fight_tick"], values[0])] = int(values[1])
            continue
        if event["kind"] != "schedule":
            continue
        values = event["value"].split(",")
        if len(values) < 6:
            continue
        path = values[0].split("#", 1)[-1]
        if path not in wanted:
            continue
        instance = values[2]
        slot = "p1" if "game.p1.mc." in instance else "p2" if "game.p2.mc." in instance else ""
        target = wanted[path]
        if slot != target["slot"]:
            continue
        rows.append({
            "source_path": path,
            "phase": values[1],
            "slot": slot,
            "parent_frame": int(values[5]),
            "child_local_frame": int(values[3]),
            "sequence": int(event["sequence"]),
            "display_tick": int(event["display_tick"]),
            "fight_tick": int(event["fight_tick"]),
            "source_instance": instance,
            "source_reported_p2_frame": int(values[5]),
            "state_actor_frame_at_tick": actor_state.get((event["fight_tick"], slot)),
            "state_actor_frame_next_tick": actor_state.get((event["fight_tick"] + 1, slot)),
        })
    return rows, actor_state


preflight = json.loads((HERE / "preflight.json").read_text())
engine_log = (RUN / "engine.log").read_text()
script_errors = [line for line in engine_log.splitlines() if "SCRIPT ERROR" in line]
batch_ok = f"MOVE_CASE_BATCH_OK {len(preflight['cases'])}" in engine_log and not script_errors
results = []
for case in preflight["cases"]:
    raw = ROOT / case["source_raw"]
    build_path = ROOT / case["source_build"]
    instrumentation = ROOT / case["source_instrumentation"]
    fixture_path = ROOT / case["native_fixture"]
    build = json.loads(build_path.read_text())
    source_fixture = json.loads((ROOT / case["source_fixture"]).read_text())
    fixture = json.loads(fixture_path.read_text())
    if sha(raw) != case["source_raw_sha256"]:
        raise SystemExit(f"source raw hash mismatch: {case['case_id']}")
    if sha(build_path) != case["source_build_sha256"]:
        raise SystemExit(f"source build hash mismatch: {case['case_id']}")
    if sha(instrumentation) != case["source_instrumentation_sha256"]:
        raise SystemExit(f"source instrumentation hash mismatch: {case['case_id']}")
    if sha(fixture_path) != case["native_fixture_sha256"]:
        raise SystemExit(f"native fixture hash mismatch: {case['case_id']}")
    if build.get("run_id") != case["run_id"] or build.get("outputs_sha256", {}).get("game/main.swf") != case["source_output_main_sha256"]:
        raise SystemExit(f"source build identity/output mismatch: {case['case_id']}")
    if source_fixture.get("id") != build.get("move_case", {}).get("id"):
        raise SystemExit(f"source fixture/build mismatch: {case['case_id']}")
    move = case["source_move_case"]
    native_input_match = (
        build.get("move_case") == move
        and fixture.get("fighters") == move.get("fighters")
        and fixture.get("setup") == move.get("setup")
        and fixture.get("inputs") == move.get("inputs")
        and fixture.get("p1_helper") == move.get("p1_helper")
        and fixture.get("p2_helper") == move.get("p2_helper")
        and fixture.get("frames") == move.get("frames")
        and build.get("configuration") == case["source_build_config"]
    )
    source, source_state = source_clip_rows(case)
    native_payload = json.loads((RUN / "out" / f"{case['case_id']}.json.clips.json").read_text())
    native = [row for row in native_payload["callback_events"] if row.get("source_path") in {target["source_path"] for target in case["targets"]}]
    target_counts = {}
    target_results = []
    for target in case["targets"]:
        path = target["source_path"]
        source_rows = [row for row in source if row["source_path"] == path]
        native_rows = [row for row in native if row["source_path"] == path]
        clock_offset = None
        if source_rows and native_rows:
            source_entry = next((row for row in source_rows if row["phase"] == "enter"), None)
            native_entry = next((row for row in native_rows if row["phase"] == "enter"), None)
            if source_entry is not None and native_entry is not None:
                clock_offset = int(native_entry["display_tick"]) - int(source_entry["fight_tick"])
        compare_parent = target["slot"] == "p2"
        source_keyed = [{
            "source_path": row["source_path"], "phase": row["phase"], "slot": row["slot"],
            "child_local_frame": int(row["child_local_frame"]),
            "normalized_tick": int(row["fight_tick"]),
            **({"parent_frame": int(row["source_reported_p2_frame"])} if compare_parent else {}),
        } for row in source_rows]
        native_keyed = [{
            "source_path": row["source_path"], "phase": row["phase"], "slot": row["slot"],
            "child_local_frame": int(row["child_placement"].get("child_local_frame", -1)),
            "normalized_tick": int(row["display_tick"]) - clock_offset if clock_offset is not None else None,
            **({"parent_frame": int(row["parent_frame"])} if compare_parent else {}),
        } for row in native_rows]
        diffs = [
            {"index": i, "source": source_keyed[i] if i < len(source_keyed) else None,
             "native": native_keyed[i] if i < len(native_keyed) else None}
            for i in range(max(len(source_keyed), len(native_keyed)))
            if (source_keyed[i] if i < len(source_keyed) else None)
            != (native_keyed[i] if i < len(native_keyed) else None)
        ]
        source_ticks = [row["fight_tick"] for row in source_rows]
        native_ticks = [int(row["display_tick"]) - clock_offset for row in native_rows] if clock_offset is not None else []
        common_count = min(len(source_ticks), len(native_ticks))
        clock_cadence_match = bool(common_count and source_ticks[:common_count] == native_ticks[:common_count])
        target_status = "exact_0diff" if native_input_match and batch_ok and source_keyed == native_keyed and source_rows else "diverged_or_invalid"
        target_counts[path] = {"source": len(source_rows), "native": len(native_rows)}
        target_results.append({
            "source_path": path,
            "slot": target["slot"],
            "status": target_status,
            "fields": ["source_path", "phase", "slot", "child_local_frame", "source-relative-tick"]
                + (["parent_frame"] if compare_parent else []),
            "native_minus_source_tick_offset": clock_offset,
            "clock_cadence_match": clock_cadence_match,
            "source_tick_count": len(source_ticks),
            "native_tick_count": len(native_ticks),
            "common_prefix_event_count": common_count if clock_cadence_match else 0,
            "source_events": source_rows,
            "native_events": native_rows,
            "differences": diffs,
            "note": "For P1, the source clip marker's sixth value is P2 current frame and is not misrepresented as P1 parent frame. Tick values are normalized using the first paired callback entry. A native proxy exit after target removal is retained as an extra native observation, not called a source marker.",
        })
    status = "exact_0diff" if native_input_match and batch_ok and all(row["status"] == "exact_0diff" for row in target_results) else "diverged_or_invalid"
    results.append({
        "case_id": case["case_id"],
        "status": status,
        "run_id": case["run_id"],
        "same_fixture_inputs_setup_helpers_and_build_config": native_input_match,
        "source": {
            "raw": case["source_raw"], "raw_sha256": sha(raw),
            "build": case["source_build"], "build_sha256": sha(build_path),
            "instrumentation": case["source_instrumentation"], "instrumentation_sha256": sha(instrumentation),
            "source_main_swf_sha256": case["source_output_main_sha256"],
            "fixture": case["source_fixture"], "fixture_sha256": sha(ROOT / case["source_fixture"]),
        },
        "native": {
            "fixture": case["native_fixture"], "fixture_sha256": sha(fixture_path),
            "runner_sha256": sha(ROOT / "godot/tests/lee_callback_exact_probe.gd"),
            "registry_probe_sha256": sha(ROOT / "godot/tests/callback_trace_registry.gd"),
            "runtime_hashes": {
                path: sha(ROOT / path) for path in (
                    "godot/fighter_runtime.gd", "godot/main.gd", "godot/helper_runtime.gd",
                    "godot/source_callback_registry.gd",
                )
            },
            "engine_log": str((RUN / "engine.log").relative_to(ROOT)),
            "engine_log_sha256": sha(RUN / "engine.log"),
            "batch_success": batch_ok,
            "script_errors": script_errors,
        },
        "fields": "Per-target fields are listed below; source P1 callback instrumentation records the P2 frame, so it is not misrepresented as P1's parent frame.",
        "target_counts": target_counts,
        "target_comparisons": target_results,
        "source_actor_state_samples": [
            {"fight_tick": tick, "slot": slot, "frame": frame}
            for (tick, slot), frame in sorted(source_state.items())
            if any(row["slot"] == slot and abs(row["fight_tick"] - tick) <= 1 for row in source)
        ],
        "source_events": source,
        "native_events": native,
    })

report = {
    "schema": "lee-callback-clip-exact-r16",
    "scope": "Two same-run/same-input clip callback comparisons. Only source path, callback phase, actor slot, parent source frame, and child local frame are compared. This is bounded callback/lifecycle evidence, not full-state or full-character parity.",
    "engine_exitcode": 0 if batch_ok else None,
    "results": results,
    "counts": {"exact_0diff": sum(row["status"] == "exact_0diff" for row in results),
               "diverged_or_invalid": sum(row["status"] != "exact_0diff" for row in results)},
}
(HERE / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report["counts"], ensure_ascii=False))
if report["counts"]["diverged_or_invalid"]:
    raise SystemExit(1)
